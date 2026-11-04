from datetime import UTC, datetime

from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User


def verify_registered_user(client, email: str) -> None:
    db_override = client.app.dependency_overrides[get_db]
    db = next(db_override())
    user = db.scalar(select(User).where(User.email == email))
    assert user is not None
    user.email_verified_at = datetime.now(UTC)
    db.commit()
