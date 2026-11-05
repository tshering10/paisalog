from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.user import User


class MonthlyBudget(Base):
    __tablename__ = "monthly_budgets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    category_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=True,
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
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

    user: Mapped["User"] = relationship()
    category: Mapped["Category | None"] = relationship()

    __table_args__ = (
        CheckConstraint("year >= 1", name="monthly_budget_year_valid"),
        CheckConstraint("month BETWEEN 1 AND 12", name="monthly_budget_month_valid"),
        CheckConstraint("amount > 0", name="monthly_budget_amount_positive"),
        UniqueConstraint(
            "user_id",
            "category_id",
            "year",
            "month",
            name="uq_monthly_budgets_user_category_period",
        ),
        Index(
            "uq_monthly_budgets_user_total_period",
            "user_id",
            "year",
            "month",
            unique=True,
            postgresql_where=category_id.is_(None),
        ),
    )
