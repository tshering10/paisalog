from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.transaction import Transaction
    from app.models.user import User


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user: Mapped["User | None"] = relationship(
        back_populates="categories",
    )

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="category",
    )

    __table_args__ = (
        CheckConstraint(
            "type IN ('income', 'expense')",
            name="category_type",
        ),
        UniqueConstraint(
            "id",
            "type",
            name="uq_categories_id_type",
        ),
        Index(
            "uq_categories_system_name_type",
            func.lower(name),
            type,
            unique=True,
            postgresql_where=user_id.is_(None),
        ),
        Index(
            "uq_categories_user_name_type",
            user_id,
            func.lower(name),
            type,
            unique=True,
            postgresql_where=user_id.is_not(None),
        ),
    )