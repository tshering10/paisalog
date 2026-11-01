"""add email verification and change

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-10-31 10:45:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: str | Sequence[str] | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "email_verified_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "pending_email",
            sa.String(length=255),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "email_verification_request_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "email_verification_request_window_started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "email_change_request_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "email_change_request_window_started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_users_pending_email_lower",
        "users",
        [sa.text("lower(pending_email)")],
    )


def downgrade() -> None:
    op.drop_index("ix_users_pending_email_lower", table_name="users")
    op.drop_column("users", "email_change_request_window_started_at")
    op.drop_column("users", "email_change_request_count")
    op.drop_column("users", "email_verification_request_window_started_at")
    op.drop_column("users", "email_verification_request_count")
    op.drop_column("users", "pending_email")
    op.drop_column("users", "email_verified_at")

