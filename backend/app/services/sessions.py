from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.models.session import UserSession


def create_session(
    db: Session,
    *,
    user_id: int,
    expires_minutes: int,
    user_agent: str | None,
    ip_address: str | None,
) -> UserSession:
    now = datetime.now(UTC)
    session = UserSession(
        id=str(uuid4()),
        user_id=user_id,
        expires_at=now + timedelta(minutes=expires_minutes),
        user_agent=user_agent[:500] if user_agent else None,
        ip_address=ip_address,
        last_used_at=now,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def touch_session(db: Session, session: UserSession) -> None:
    session.last_used_at = datetime.now(UTC)
    db.commit()


def revoke_session(db: Session, session: UserSession) -> None:
    if session.revoked_at is None:
        session.revoked_at = datetime.now(UTC)
        db.commit()


def revoke_other_sessions(
    db: Session,
    *,
    user_id: int,
    current_session_id: str,
) -> None:
    db.execute(
        update(UserSession)
        .where(
            UserSession.user_id == user_id,
            UserSession.id != current_session_id,
            UserSession.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(UTC))
    )
    db.commit()


def list_active_sessions(db: Session, user_id: int) -> list[UserSession]:
    now = datetime.now(UTC)
    db.execute(
        delete(UserSession).where(
            UserSession.expires_at <= now,
            UserSession.user_id == user_id,
        )
    )
    db.commit()
    return list(
        db.scalars(
            select(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > now,
            )
            .order_by(UserSession.last_used_at.desc())
        )
    )
