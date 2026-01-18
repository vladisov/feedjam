"""Add ranking tables and rank_score column

Revision ID: 105521347a4e
Revises: 06224794abbf
Create Date: 2025-01-17

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '105521347a4e'
down_revision = '06224794abbf'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_interests table
    op.create_table(
        'user_interests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('topic', sa.String(100), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_interests_id'), 'user_interests', ['id'], unique=False)
    op.create_index(op.f('ix_user_interests_user_id'), 'user_interests', ['user_id'], unique=False)

    # Create user_like_history table
    op.create_table(
        'user_like_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('source_name', sa.String(255), nullable=False),
        sa.Column('like_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('dislike_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_like_history_id'), 'user_like_history', ['id'], unique=False)
    op.create_index(op.f('ix_user_like_history_user_id'), 'user_like_history', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_like_history_source_name'), 'user_like_history', ['source_name'], unique=False)

    # Add rank_score column to user_feed_items
    op.add_column('user_feed_items', sa.Column('rank_score', sa.Float(), nullable=False, server_default='0.0'))


def downgrade() -> None:
    # Remove rank_score column from user_feed_items
    op.drop_column('user_feed_items', 'rank_score')

    # Drop user_like_history table
    op.drop_index(op.f('ix_user_like_history_source_name'), table_name='user_like_history')
    op.drop_index(op.f('ix_user_like_history_user_id'), table_name='user_like_history')
    op.drop_index(op.f('ix_user_like_history_id'), table_name='user_like_history')
    op.drop_table('user_like_history')

    # Drop user_interests table
    op.drop_index(op.f('ix_user_interests_user_id'), table_name='user_interests')
    op.drop_index(op.f('ix_user_interests_id'), table_name='user_interests')
    op.drop_table('user_interests')
