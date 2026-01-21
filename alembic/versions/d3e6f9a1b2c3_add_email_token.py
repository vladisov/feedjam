"""Add email_token field to users table.

Revision ID: d3e6f9a1b2c3
Revises: c2d5e7f8g9h0
Create Date: 2026-01-19

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d3e6f9a1b2c3"
down_revision: str | None = "c2d5e7f8g9h0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email_token", sa.String(32), nullable=True))
    op.create_index("ix_users_email_token", "users", ["email_token"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_email_token", table_name="users")
    op.drop_column("users", "email_token")
