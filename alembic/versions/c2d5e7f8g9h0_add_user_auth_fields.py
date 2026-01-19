"""Add user auth fields (email, hashed_password, is_verified)

Revision ID: c2d5e7f8g9h0
Revises: b1e4ca13f10d
Create Date: 2026-01-19

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c2d5e7f8g9h0"
down_revision: str | None = "b1e4ca13f10d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("hashed_password", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"))

    # Create unique index on email
    op.create_index("ix_users_email", "users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_column("users", "is_verified")
    op.drop_column("users", "hashed_password")
    op.drop_column("users", "email")
