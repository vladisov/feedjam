"""Add user API keys

Revision ID: a1b2c3d4e5f6
Revises: 60118ec288f9
Create Date: 2026-01-18

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "60118ec288f9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("openai_api_key", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "openai_api_key")
