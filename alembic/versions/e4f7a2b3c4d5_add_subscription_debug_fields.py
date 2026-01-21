"""Add subscription debug fields (last_error, item_count)

Revision ID: e4f7a2b3c4d5
Revises: d3e6f9a1b2c3
Create Date: 2026-01-20

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e4f7a2b3c4d5"
down_revision: str | None = "d3e6f9a1b2c3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("subscriptions", sa.Column("last_error", sa.String(500), nullable=True))
    op.add_column("subscriptions", sa.Column("item_count", sa.Integer(), nullable=True, server_default="0"))


def downgrade() -> None:
    op.drop_column("subscriptions", "item_count")
    op.drop_column("subscriptions", "last_error")
