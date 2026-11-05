"""add monthly budgets

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: str | Sequence[str] | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "monthly_budgets",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("category_id", sa.BigInteger(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "category_id",
            "year",
            "month",
            name="uq_monthly_budgets_user_category_period",
        ),
        sa.CheckConstraint("year >= 1", name="monthly_budget_year_valid"),
        sa.CheckConstraint(
            "month BETWEEN 1 AND 12",
            name="monthly_budget_month_valid",
        ),
        sa.CheckConstraint(
            "amount > 0",
            name="monthly_budget_amount_positive",
        ),
    )
    op.create_index(
        "uq_monthly_budgets_user_total_period",
        "monthly_budgets",
        ["user_id", "year", "month"],
        unique=True,
        postgresql_where=sa.text("category_id IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_monthly_budgets_user_total_period",
        table_name="monthly_budgets",
    )
    op.drop_table("monthly_budgets")
