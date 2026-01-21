"""Add onboarding_completed field to users table.

Revision ID: f5g8h3i4j5k6
Revises: e4f7a2b3c4d5
Create Date: 2026-01-20

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f5g8h3i4j5k6"
down_revision: str | None = "e4f7a2b3c4d5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add column with default True for existing users (they skip onboarding)
    op.add_column(
        "users",
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default="true"),
    )


def downgrade() -> None:
    op.drop_column("users", "onboarding_completed")
