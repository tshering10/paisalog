"""add auth security state

Revision ID: 9b8c7d6e5f4a
Revises: 8a7b6c5d4e3f
Create Date: 2026-10-22 18:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "9b8c7d6e5f4a"
down_revision: str | Sequence[str] | None = "8a7b6c5d4e3f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "token_version",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "password_reset_request_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "password_reset_request_window_started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "password_reset_request_window_started_at")
    op.drop_column("users", "password_reset_request_count")
    op.drop_column("users", "token_version")
