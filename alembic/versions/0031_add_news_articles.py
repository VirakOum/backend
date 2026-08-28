"""add_news_articles

Revision ID: 0031_add_news_articles
Revises: 0030_add_currency_to_trips_and_bookings
Create Date: 2026-08-28 17:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '0031_add_news_articles'
down_revision = '0030_add_currency_to_trips_and_bookings'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'news_articles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('title_kh', sa.String(length=255), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('summary_kh', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(length=500), nullable=False),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('source_name', sa.String(length=100), nullable=False, server_default='Fresh News'),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='Breaking News'),
        sa.Column('is_breaking', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('published_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_news_articles_is_active', 'news_articles', ['is_active'])
    op.create_index('ix_news_articles_published_at', 'news_articles', ['published_at'])


def downgrade() -> None:
    op.drop_index('ix_news_articles_published_at', table_name='news_articles')
    op.drop_index('ix_news_articles_is_active', table_name='news_articles')
    op.drop_table('news_articles')
