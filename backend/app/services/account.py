from datetime import UTC, datetime

from sqlalchemy import delete, update
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.account_action_token import AccountActionToken
from app.models.category import Category
from app.models.password_reset_token import PasswordResetToken
from app.models.session import UserSession
from app.models.transaction import Transaction
from app.models.user import User


class AccountPasswordIncorrectError(Exception):
    """Raised when an account action receives the wrong password."""


def _verify_account_password(user: User, password: str) -> None:
    if not verify_password(password, user.hashed_password):
        raise AccountPasswordIncorrectError


def deactivate_account(db: Session, user: User, password: str) -> None:
    _verify_account_password(user, password)
    now = datetime.now(UTC)
    user.is_active = False
    user.token_version += 1
    db.execute(
        update(UserSession)
        .where(UserSession.user_id == user.id, UserSession.revoked_at.is_(None))
        .values(revoked_at=now)
    )
    db.commit()


def delete_account(db: Session, user: User, password: str) -> None:
    _verify_account_password(user, password)
    user_id = user.id
    db.execute(delete(Transaction).where(Transaction.user_id == user_id))
    db.execute(delete(Category).where(Category.user_id == user_id))
    db.execute(delete(UserSession).where(UserSession.user_id == user_id))
    db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user_id))
    db.execute(delete(AccountActionToken).where(AccountActionToken.user_id == user_id))
    db.delete(user)
    db.commit()
