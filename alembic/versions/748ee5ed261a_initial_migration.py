"""Initial migration

Revision ID: 748ee5ed261a
Revises:
Create Date: 2023-11-25 16:18:08.946057

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '748ee5ed261a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('feed_items',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('title', sa.String(), nullable=True),
                    sa.Column('link', sa.String(), nullable=True),
                    sa.Column('created_at', sa.DateTime(),
                              server_default=sa.text('now()'), nullable=True),
                    sa.Column('updated_at', sa.DateTime(),
                              server_default=sa.text('now()'), nullable=True),
                    sa.Column('published', sa.DateTime(),
                              server_default=sa.text('now()'), nullable=True),
                    sa.Column('local_id', sa.String(), nullable=True),
                    sa.Column('description', sa.String(), nullable=True),
                    sa.Column('article_url', sa.String(), nullable=True),
                    sa.Column('comments_url', sa.String(), nullable=True),
                    sa.Column('points', sa.Integer(),
                              server_default='0', nullable=True),
                    sa.Column('views', sa.Integer(),
                              server_default='0', nullable=True),
                    sa.Column('num_comments', sa.Integer(), nullable=True),
                    sa.Column('summary', sa.String(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('sources',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(), nullable=True),
                    sa.Column('resource_url', sa.String(), nullable=True),
                    sa.Column('created_at', sa.DateTime(),
                              server_default=sa.text('now()'), nullable=True),
                    sa.Column('is_active', sa.Boolean(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_sources_id'), 'sources', ['id'], unique=False)
    op.create_index(op.f('ix_sources_name'), 'sources', ['name'], unique=True)
    op.create_index(op.f('ix_sources_resource_url'),
                    'sources', ['resource_url'], unique=True)
    op.create_table('user_feed_item_states',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('hide', sa.Boolean(),
                              server_default='false', nullable=True),
                    sa.Column('read', sa.Boolean(),
                              server_default='false', nullable=True),
                    sa.Column('star', sa.Boolean(),
                              server_default='false', nullable=True),
                    sa.Column('like', sa.Boolean(),
                              server_default='false', nullable=True),
                    sa.Column('dislike', sa.Boolean(),
                              server_default='false', nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_user_feed_item_states_id'),
                    'user_feed_item_states', ['id'], unique=False)
    op.create_table('users',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('handle', sa.String(), nullable=True),
                    sa.Column('is_active', sa.Boolean(), nullable=True),
                    sa.Column('created_at', sa.DateTime(),
                              server_default=sa.text('now()'), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_table('feeds',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('created_at', sa.DateTime(),
                              server_default=sa.text('now()'), nullable=True),
                    sa.Column('updated_at', sa.DateTime(),
                              server_default=sa.text('now()'), nullable=True),
                    sa.Column('source_id', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_feeds_id'), 'feeds', ['id'], unique=False)
    op.create_table('subscriptions',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('is_active', sa.Boolean(), nullable=True),
                    sa.Column('user_id', sa.Integer(), nullable=True),
                    sa.Column('source_id', sa.Integer(), nullable=True),
                    sa.Column('created_at', sa.DateTime(),
                              server_default=sa.text('now()'), nullable=True),
                    sa.Column('last_run', sa.DateTime(), nullable=True),
                    sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_subscriptions_id'),
                    'subscriptions', ['id'], unique=False)
    op.create_index(op.f('ix_subscriptions_source_id'),
                    'subscriptions', ['source_id'], unique=False)
    op.create_index(op.f('ix_subscriptions_user_id'),
                    'subscriptions', ['user_id'], unique=False)
    op.create_table('user_feeds',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('is_active', sa.Boolean(), nullable=True),
                    sa.Column('created_at', sa.DateTime(),
                              server_default=sa.text('now()'), nullable=True),
                    sa.Column('updated_at', sa.DateTime(),
                              server_default=sa.text('now()'), nullable=True),
                    sa.Column('user_id', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_user_feeds_id'),
                    'user_feeds', ['id'], unique=False)
    op.create_table('feed_feeditem',
                    sa.Column('feed_id', sa.Integer(), nullable=True),
                    sa.Column('feeditem_id', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['feed_id'], ['feeds.id'], ),
                    sa.ForeignKeyConstraint(
                        ['feeditem_id'], ['feed_items.id'], )
                    )
    op.create_table('runs',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('created_at', sa.DateTime(),
                              server_default=sa.text('now()'), nullable=True),
                    sa.Column('status', sa.String(), nullable=True),
                    sa.Column('subscription_id', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['subscription_id'], [
                                            'subscriptions.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_runs_id'), 'runs', ['id'], unique=False)
    op.create_table('user_feed_items',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('created_at', sa.DateTime(),
                              server_default=sa.text('now()'), nullable=True),
                    sa.Column('updated_at', sa.DateTime(),
                              server_default=sa.text('now()'), nullable=True),
                    sa.Column('title', sa.String(), nullable=True),
                    sa.Column('summary', sa.String(), nullable=True),
                    sa.Column('source_name', sa.String(), nullable=True),
                    sa.Column('description', sa.String(), nullable=True),
                    sa.Column('article_url', sa.String(), nullable=True),
                    sa.Column('comments_url', sa.String(), nullable=True),
                    sa.Column('points', sa.Integer(),
                              server_default='0', nullable=True),
                    sa.Column('views', sa.Integer(),
                              server_default='0', nullable=True),
                    sa.Column('feed_item_id', sa.Integer(), nullable=True),
                    sa.Column('user_id', sa.Integer(), nullable=True),
                    sa.Column('user_feed_id', sa.Integer(), nullable=True),
                    sa.Column('state_id', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(
                        ['feed_item_id'], ['feed_items.id'], ),
                    sa.ForeignKeyConstraint(
                        ['state_id'], ['user_feed_item_states.id'], ),
                    sa.ForeignKeyConstraint(
                        ['user_feed_id'], ['user_feeds.id'], ),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_user_feed_items_id'),
                    'user_feed_items', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_user_feed_items_id'), table_name='user_feed_items')
    op.drop_table('user_feed_items')
    op.drop_index(op.f('ix_runs_id'), table_name='runs')
    op.drop_table('runs')
    op.drop_table('feed_feeditem')
    op.drop_index(op.f('ix_user_feeds_id'), table_name='user_feeds')
    op.drop_table('user_feeds')
    op.drop_index(op.f('ix_subscriptions_user_id'), table_name='subscriptions')
    op.drop_index(op.f('ix_subscriptions_source_id'),
                  table_name='subscriptions')
    op.drop_index(op.f('ix_subscriptions_id'), table_name='subscriptions')
    op.drop_table('subscriptions')
    op.drop_index(op.f('ix_feeds_id'), table_name='feeds')
    op.drop_table('feeds')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_user_feed_item_states_id'),
                  table_name='user_feed_item_states')
    op.drop_table('user_feed_item_states')
    op.drop_index(op.f('ix_sources_resource_url'), table_name='sources')
    op.drop_index(op.f('ix_sources_name'), table_name='sources')
    op.drop_index(op.f('ix_sources_id'), table_name='sources')
    op.drop_table('sources')
    op.drop_table('feed_items')
    # ### end Alembic commands ###
