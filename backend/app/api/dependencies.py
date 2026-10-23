from datetime import UTC, datetime
from typing import Annotated

import jwt
from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.session import UserSession
from app.models.user import User

DbSession = Annotated[Session, Depends(get_db)]


def get_current_session(
    db: DbSession,
    access_token: Annotated[str | None, Cookie()] = None,
) -> UserSession:
    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id, token_version, session_id = decode_access_token(
            token=access_token,
            secret_key=get_settings().secret_key,
        )
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    session = db.scalar(
        select(UserSession).where(
            UserSession.id == session_id,
            UserSession.user_id == user_id,
        )
    )
    user = db.scalar(select(User).where(User.id == user_id))
    if (
        session is None
        or user is None
        or not user.is_active
        or user.token_version != token_version
        or session.revoked_at is not None
        or session.expires_at <= datetime.now(UTC)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    session.last_used_at = datetime.now(UTC)
    db.commit()
    return session


def get_current_user(
    current_session: Annotated[UserSession, Depends(get_current_session)],
) -> User:
    return current_session.user


CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentSession = Annotated[UserSession, Depends(get_current_session)]
