import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.account_action_token import AccountActionToken
from app.models.user import User

EMAIL_VERIFICATION_PURPOSE = "email_verification"
EMAIL_CHANGE_PURPOSE = "email_change"


class InvalidVerificationTokenError(Exception):
    """Raised when an email verification token is invalid, expired, or already used."""


class InvalidEmailChangeTokenError(Exception):
    """Raised when an email change token is invalid, expired, or already used."""


class EmailChangePasswordIncorrectError(Exception):
    """Raised when current password check fails during email change request."""


class EmailAlreadyInUseError(Exception):
    """Raised when the requested email is already used or pending by another account."""


class SameEmailError(Exception):
    """Raised when the new email is identical to current email."""


def create_email_verification_token(
    db: Session,
    *,
    user: User,
    expires_minutes: int,
    rate_limit_count: int,
    rate_limit_window_minutes: int,
) -> str | None:
    locked_user = db.scalar(select(User).where(User.id == user.id).with_for_update())
    if locked_user is None or not locked_user.is_active or locked_user.email_verified_at is not None:
        return None

    now = datetime.now(UTC)
    window_started = locked_user.email_verification_request_window_started_at
    if (
        window_started is None
        or window_started + timedelta(minutes=rate_limit_window_minutes) <= now
    ):
        locked_user.email_verification_request_count = 0
        locked_user.email_verification_request_window_started_at = now

    if locked_user.email_verification_request_count >= rate_limit_count:
        db.commit()
        return None

    locked_user.email_verification_request_count += 1
    db.execute(
        update(AccountActionToken)
        .where(
            AccountActionToken.user_id == locked_user.id,
            AccountActionToken.purpose == EMAIL_VERIFICATION_PURPOSE,
            AccountActionToken.used_at.is_(None),
        )
        .values(used_at=now)
    )
    db.execute(
        delete(AccountActionToken).where(
            (AccountActionToken.used_at.is_not(None))
            | (AccountActionToken.expires_at <= now)
        )
    )

    raw_token = secrets.token_urlsafe(32)
    db.add(
        AccountActionToken(
            user_id=locked_user.id,
            purpose=EMAIL_VERIFICATION_PURPOSE,
            token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
            expires_at=now + timedelta(minutes=expires_minutes),
        )
    )
    db.commit()
    return raw_token


def verify_email(db: Session, *, raw_token: str) -> User:
    now = datetime.now(UTC)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    token = db.scalar(
        select(AccountActionToken)
        .where(
            AccountActionToken.token_hash == token_hash,
            AccountActionToken.purpose == EMAIL_VERIFICATION_PURPOSE,
        )
        .with_for_update()
    )
    if token is None or token.used_at is not None or token.expires_at <= now:
        raise InvalidVerificationTokenError

    user = db.scalar(select(User).where(User.id == token.user_id).with_for_update())
    if user is None or not user.is_active:
        raise InvalidVerificationTokenError

    user.email_verified_at = now
    token.used_at = now
    db.execute(
        delete(AccountActionToken).where(
            (AccountActionToken.used_at.is_not(None))
            | (AccountActionToken.expires_at <= now)
        )
    )
    db.commit()
    db.refresh(user)
    return user


def request_email_change(
    db: Session,
    *,
    user: User,
    new_email: str,
    password: str,
    expires_minutes: int,
    rate_limit_count: int,
    rate_limit_window_minutes: int,
) -> tuple[str | None, str]:
    if not verify_password(password, user.hashed_password):
        raise EmailChangePasswordIncorrectError

    normalized_new_email = new_email.strip().lower()
    if normalized_new_email == user.email.strip().lower():
        raise SameEmailError

    # Check against primary emails
    existing_primary = db.scalar(
        select(User).where(func.lower(User.email) == normalized_new_email)
    )
    if existing_primary is not None:
        raise EmailAlreadyInUseError

    # Check against pending emails of other users
    existing_pending = db.scalar(
        select(User).where(
            func.lower(User.pending_email) == normalized_new_email,
            User.id != user.id,
        )
    )
    if existing_pending is not None:
        raise EmailAlreadyInUseError

    locked_user = db.scalar(select(User).where(User.id == user.id).with_for_update())
    if locked_user is None or not locked_user.is_active:
        raise InvalidEmailChangeTokenError

    now = datetime.now(UTC)
    window_started = locked_user.email_change_request_window_started_at
    if (
        window_started is None
        or window_started + timedelta(minutes=rate_limit_window_minutes) <= now
    ):
        locked_user.email_change_request_count = 0
        locked_user.email_change_request_window_started_at = now

    if locked_user.email_change_request_count >= rate_limit_count:
        db.commit()
        return None, normalized_new_email

    locked_user.email_change_request_count += 1
    locked_user.pending_email = normalized_new_email

    db.execute(
        update(AccountActionToken)
        .where(
            AccountActionToken.user_id == locked_user.id,
            AccountActionToken.purpose == EMAIL_CHANGE_PURPOSE,
            AccountActionToken.used_at.is_(None),
        )
        .values(used_at=now)
    )
    db.execute(
        delete(AccountActionToken).where(
            (AccountActionToken.used_at.is_not(None))
            | (AccountActionToken.expires_at <= now)
        )
    )

    raw_token = secrets.token_urlsafe(32)
    db.add(
        AccountActionToken(
            user_id=locked_user.id,
            purpose=EMAIL_CHANGE_PURPOSE,
            token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
            expires_at=now + timedelta(minutes=expires_minutes),
        )
    )
    db.commit()
    return raw_token, normalized_new_email


def confirm_email_change(db: Session, *, raw_token: str) -> User:
    now = datetime.now(UTC)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    token = db.scalar(
        select(AccountActionToken)
        .where(
            AccountActionToken.token_hash == token_hash,
            AccountActionToken.purpose == EMAIL_CHANGE_PURPOSE,
        )
        .with_for_update()
    )
    if token is None or token.used_at is not None or token.expires_at <= now:
        raise InvalidEmailChangeTokenError

    user = db.scalar(select(User).where(User.id == token.user_id).with_for_update())
    if user is None or not user.is_active or not user.pending_email:
        raise InvalidEmailChangeTokenError

    # Verify pending email wasn't taken while waiting
    existing_primary = db.scalar(
        select(User).where(
            func.lower(User.email) == func.lower(user.pending_email),
            User.id != user.id,
        )
    )
    if existing_primary is not None:
        user.pending_email = None
        token.used_at = now
        db.commit()
        raise EmailAlreadyInUseError

    user.email = user.pending_email
    user.pending_email = None
    user.email_verified_at = now
    user.token_version += 1
    token.used_at = now

    db.execute(
        delete(AccountActionToken).where(
            (AccountActionToken.used_at.is_not(None))
            | (AccountActionToken.expires_at <= now)
        )
    )
    db.commit()
    db.refresh(user)
    return user

