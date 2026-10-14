from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password

class EmailAlreadyRegisteredError(Exception):
    """Raised when a user tries to register an existing email address."""
class InvalidCredentialsError(Exception):
    """Raised when login credentials are invalid."""


def register_user(db: Session, user_data: UserCreate) -> User:
    normalized_email = str(user_data.email).strip().lower()

    existing_user = db.scalar(
        select(User).where(User.email == normalized_email)
    )

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
    user = db.scalar(
        select(User).where(User.email == normalized_email)
    )
    
    if user is None or not verify_password(
        password, user.hashed_password,
    ):
        raise InvalidCredentialsError
    
    if not user.is_active:
        raise InvalidCredentialsError
    
    return user