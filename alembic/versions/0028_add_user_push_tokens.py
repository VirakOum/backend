"""add_user_push_tokens

Revision ID: 0028_add_user_push_tokens
Revises: 67daf2cb89a5
Create Date: 2026-08-25 22:35:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '0028_add_user_push_tokens'
down_revision = '0027_add_system_messages'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'user_push_tokens',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('push_token', sa.String(length=512), nullable=False),
        sa.Column('platform', sa.String(length=30), nullable=False, server_default='android'),
        sa.Column('device_id', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_user_push_tokens_user_id', 'user_push_tokens', ['user_id'])
    op.create_index('ix_user_push_tokens_push_token', 'user_push_tokens', ['push_token'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_user_push_tokens_push_token', table_name='user_push_tokens')
    op.drop_index('ix_user_push_tokens_user_id', table_name='user_push_tokens')
    op.drop_table('user_push_tokens')
