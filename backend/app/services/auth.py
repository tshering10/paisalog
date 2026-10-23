import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.password_reset_token import PasswordResetToken
from app.models.session import UserSession
from app.models.user import User
from app.schemas.user import UserCreate, UserProfileUpdate


class EmailAlreadyRegisteredError(Exception):
    """Raised when a user tries to register an existing email address."""


class InvalidCredentialsError(Exception):
    """Raised when login credentials are invalid."""


class AccountDeactivatedError(Exception):
    """Raised when valid credentials belong to a deactivated account."""


class CurrentPasswordIncorrectError(Exception):
    """Raised when the current password is incorrect."""


class InvalidPasswordResetTokenError(Exception):
    """Raised when a password reset token is invalid or expired."""


def register_user(db: Session, user_data: UserCreate) -> User:
    normalized_email = str(user_data.email).strip().lower()

    existing_user = db.scalar(select(User).where(User.email == normalized_email))

    if existing_user is not None:
        raise EmailAlreadyRegisteredError

    user = User(
        email=normalized_email,
        full_name=user_data.full_name.strip(),
        hashed_password=hash_password(user_data.password),
        is_active=True,
    )

    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise EmailAlreadyRegisteredError from None

    db.refresh(user)
    return user


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User:
    normalized_email = email.strip().lower()
    user = db.scalar(select(User).where(User.email == normalized_email))

    if user is None or not verify_password(
        password,
        user.hashed_password,
    ):
        raise InvalidCredentialsError

    if not user.is_active:
        raise AccountDeactivatedError

    return user


def update_profile(
    db: Session,
    user: User,
    profile_data: UserProfileUpdate,
) -> User:
    full_name = profile_data.full_name.strip()
    user.full_name = full_name
    db.commit()
    db.refresh(user)
    return user


def change_password(
    db: Session,
    user: User,
    current_password: str,
    new_password: str,
) -> None:
    if not verify_password(current_password, user.hashed_password):
        raise CurrentPasswordIncorrectError

    user.hashed_password = hash_password(new_password)
    user.token_version += 1
    db.execute(
        update(UserSession)
        .where(UserSession.user_id == user.id)
        .values(revoked_at=datetime.now(UTC))
    )
    db.commit()


def create_password_reset_token(
    db: Session,
    user: User,
    expires_minutes: int,
    rate_limit_count: int,
    rate_limit_window_minutes: int,
) -> str | None:
    user = db.scalar(select(User).where(User.id == user.id).with_for_update())
    if user is None or not user.is_active:
        return None

    now = datetime.now(UTC)
    window_start = user.password_reset_request_window_started_at
    if (
        window_start is None
        or window_start + timedelta(minutes=rate_limit_window_minutes) <= now
    ):
        user.password_reset_request_count = 0
        user.password_reset_request_window_started_at = now

    if user.password_reset_request_count >= rate_limit_count:
        db.commit()
        return None

    user.password_reset_request_count += 1
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        )
        .values(used_at=now)
    )
    db.execute(
        delete(PasswordResetToken).where(
            (PasswordResetToken.used_at.is_not(None))
            | (PasswordResetToken.expires_at <= now)
        )
    )
    token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=now + timedelta(minutes=expires_minutes),
    )
    db.add(token)
    db.commit()
    return raw_token


def reset_password(
    db: Session,
    raw_token: str,
    new_password: str,
) -> None:
    now = datetime.now(UTC)
    db.execute(
        delete(PasswordResetToken).where(
            (PasswordResetToken.used_at.is_not(None))
            | (PasswordResetToken.expires_at <= now)
        )
    )
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    token = db.scalar(
        select(PasswordResetToken)
        .where(PasswordResetToken.token_hash == token_hash)
        .with_for_update()
    )

    if token is None or token.used_at is not None or token.expires_at <= now:
        raise InvalidPasswordResetTokenError

    user = db.get(User, token.user_id)
    if user is None or not user.is_active:
        raise InvalidPasswordResetTokenError

    user.hashed_password = hash_password(new_password)
    user.token_version += 1
    token.used_at = now
    db.execute(
        update(UserSession).where(UserSession.user_id == user.id).values(revoked_at=now)
    )
    db.commit()
