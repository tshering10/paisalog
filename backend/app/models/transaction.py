from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.user import User


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    category_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship(
        back_populates="transactions",
    )

    category: Mapped["Category"] = relationship(
        back_populates="transactions",
    )

    __table_args__ = (
        CheckConstraint(
            "type IN ('income', 'expense')",
            name="transaction_type",
        ),
        CheckConstraint(
            "amount > 0",
            name="transaction_amount_positive",
        ),
        ForeignKeyConstraint(
            ["category_id", "type"],
            ["categories.id", "categories.type"],
            name="fk_transactions_category_type",
            ondelete="RESTRICT",
        ),
        Index(
            "ix_transactions_user_id_transaction_date",
            "user_id",
            "transaction_date",
        ),
    )