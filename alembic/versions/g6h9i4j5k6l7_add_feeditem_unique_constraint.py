"""Add unique constraint on feed_items (local_id, source_name).

Revision ID: g6h9i4j5k6l7
Revises: f5g8h3i4j5k6
Create Date: 2026-01-20

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "g6h9i4j5k6l7"
down_revision = "f5g8h3i4j5k6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Identify duplicate feed_item ids to remove (keep oldest by id)
    # First, clean up references to duplicates in association tables and user items
    op.execute(
        """
        WITH duplicates AS (
            SELECT id
            FROM feed_items
            WHERE local_id IS NOT NULL
            AND id NOT IN (
                SELECT MIN(id)
                FROM feed_items
                WHERE local_id IS NOT NULL
                GROUP BY local_id, source_name
            )
        )
        DELETE FROM feed_feeditem WHERE feeditem_id IN (SELECT id FROM duplicates)
        """
    )

    op.execute(
        """
        WITH duplicates AS (
            SELECT id
            FROM feed_items
            WHERE local_id IS NOT NULL
            AND id NOT IN (
                SELECT MIN(id)
                FROM feed_items
                WHERE local_id IS NOT NULL
                GROUP BY local_id, source_name
            )
        )
        DELETE FROM user_feed_items WHERE feed_item_id IN (SELECT id FROM duplicates)
        """
    )

    op.execute(
        """
        WITH duplicates AS (
            SELECT id
            FROM feed_items
            WHERE local_id IS NOT NULL
            AND id NOT IN (
                SELECT MIN(id)
                FROM feed_items
                WHERE local_id IS NOT NULL
                GROUP BY local_id, source_name
            )
        )
        DELETE FROM user_item_states WHERE feed_item_id IN (SELECT id FROM duplicates)
        """
    )

    # Now remove duplicate feed_items
    op.execute(
        """
        DELETE FROM feed_items
        WHERE local_id IS NOT NULL
        AND id NOT IN (
            SELECT MIN(id)
            FROM feed_items
            WHERE local_id IS NOT NULL
            GROUP BY local_id, source_name
        )
        """
    )

    # Drop the existing non-unique index
    op.drop_index("ix_feed_items_local_id_source", table_name="feed_items")

    # Create partial unique index (only where local_id is not null)
    op.execute(
        """
        CREATE UNIQUE INDEX ix_feed_items_local_id_source_unique
        ON feed_items (local_id, source_name)
        WHERE local_id IS NOT NULL
        """
    )


def downgrade() -> None:
    # Drop the unique index
    op.drop_index("ix_feed_items_local_id_source_unique", table_name="feed_items")

    # Recreate the non-unique index
    op.create_index(
        "ix_feed_items_local_id_source",
        "feed_items",
        ["local_id", "source_name"],
    )
