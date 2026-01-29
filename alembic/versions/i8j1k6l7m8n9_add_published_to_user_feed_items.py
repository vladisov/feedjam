"""Add published column to user_feed_items.

Revision ID: i8j1k6l7m8n9
Revises: h7i0j5k6l7m8
Create Date: 2026-01-29

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "i8j1k6l7m8n9"
down_revision = "h7i0j5k6l7m8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_feed_items", sa.Column("published", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("user_feed_items", "published")
