import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.models.account_action_token import AccountActionToken
from app.models.session import UserSession
from app.models.user import User

REACTIVATION_PURPOSE = "account_reactivation"


class InvalidReactivationTokenError(Exception):
    """Raised when a reactivation token is invalid, expired, or already used."""


def create_reactivation_token(
    db: Session,
    *,
    user: User,
    expires_minutes: int,
    rate_limit_count: int,
    rate_limit_window_minutes: int,
) -> str | None:
    locked_user = db.scalar(select(User).where(User.id == user.id).with_for_update())
    if locked_user is None or locked_user.is_active:
        return None

    now = datetime.now(UTC)
    window_started = locked_user.reactivation_request_window_started_at
    if (
        window_started is None
        or window_started + timedelta(minutes=rate_limit_window_minutes) <= now
    ):
        locked_user.reactivation_request_count = 0
        locked_user.reactivation_request_window_started_at = now

    if locked_user.reactivation_request_count >= rate_limit_count:
        db.commit()
        return None

    locked_user.reactivation_request_count += 1
    db.execute(
        update(AccountActionToken)
        .where(
            AccountActionToken.user_id == locked_user.id,
            AccountActionToken.purpose == REACTIVATION_PURPOSE,
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
            purpose=REACTIVATION_PURPOSE,
            token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
            expires_at=now + timedelta(minutes=expires_minutes),
        )
    )
    db.commit()
    return raw_token


def reactivate_account(db: Session, *, raw_token: str) -> None:
    now = datetime.now(UTC)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    token = db.scalar(
        select(AccountActionToken)
        .where(
            AccountActionToken.token_hash == token_hash,
            AccountActionToken.purpose == REACTIVATION_PURPOSE,
        )
        .with_for_update()
    )
    if token is None or token.used_at is not None or token.expires_at <= now:
        raise InvalidReactivationTokenError

    user = db.scalar(select(User).where(User.id == token.user_id).with_for_update())
    if user is None or user.is_active:
        raise InvalidReactivationTokenError

    user.is_active = True
    token.used_at = now
    db.execute(
        delete(AccountActionToken).where(
            (AccountActionToken.used_at.is_not(None))
            | (AccountActionToken.expires_at <= now)
        )
    )
    db.execute(
        update(UserSession).where(UserSession.user_id == user.id).values(revoked_at=now)
    )
    db.commit()
