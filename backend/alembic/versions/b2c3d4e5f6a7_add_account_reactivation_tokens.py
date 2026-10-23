"""add account reactivation tokens

Revision ID: b2c3d4e5f6a7
Revises: af1b2c3d4e5f
Create Date: 2026-10-23 21:50:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "af1b2c3d4e5f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "reactivation_request_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "reactivation_request_window_started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.create_table(
        "account_action_tokens",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("purpose", sa.String(length=50), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        "ix_account_action_tokens_user_purpose",
        "account_action_tokens",
        ["user_id", "purpose"],
    )
    op.create_index(
        "ix_account_action_tokens_expires_at", "account_action_tokens", ["expires_at"]
    )


def downgrade() -> None:
    op.drop_index(
        "ix_account_action_tokens_expires_at", table_name="account_action_tokens"
    )
    op.drop_index(
        "ix_account_action_tokens_user_purpose", table_name="account_action_tokens"
    )
    op.drop_table("account_action_tokens")
    op.drop_column("users", "reactivation_request_window_started_at")
    op.drop_column("users", "reactivation_request_count")
