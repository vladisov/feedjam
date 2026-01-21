"""Remove user_feed_item_states table - state now comes from user_item_states.

Revision ID: h7i0j5k6l7m8
Revises: g6h9i4j5k6l7
Create Date: 2026-01-20

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "h7i0j5k6l7m8"
down_revision = "g6h9i4j5k6l7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the state_id foreign key and column from user_feed_items
    op.drop_constraint(
        "user_feed_items_state_id_fkey", "user_feed_items", type_="foreignkey"
    )
    op.drop_column("user_feed_items", "state_id")

    # Drop the user_feed_item_states table
    op.drop_table("user_feed_item_states")


def downgrade() -> None:
    # Recreate the user_feed_item_states table
    op.create_table(
        "user_feed_item_states",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("hide", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("star", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("like", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("dislike", sa.Boolean(), nullable=False, server_default="false"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_feed_item_states_id", "user_feed_item_states", ["id"])

    # Add state_id column back to user_feed_items
    op.add_column(
        "user_feed_items",
        sa.Column("state_id", sa.Integer(), nullable=True),
    )

    # Create default state entries for existing items
    op.execute(
        """
        INSERT INTO user_feed_item_states (id)
        SELECT id FROM user_feed_items
        """
    )

    # Update state_id to point to the new states
    op.execute(
        """
        UPDATE user_feed_items SET state_id = id
        """
    )

    # Make state_id non-nullable and add foreign key
    op.alter_column("user_feed_items", "state_id", nullable=False)
    op.create_foreign_key(
        "user_feed_items_state_id_fkey",
        "user_feed_items",
        "user_feed_item_states",
        ["state_id"],
        ["id"],
    )
