"""expand news_articles text columns

Revision ID: 0034_expand_news_article_fields
Revises: 0033_add_app_version_configs
Create Date: 2026-10-14 13:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0034_expand_news_article_fields"
down_revision = "0033_add_app_version_configs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("news_articles") as batch_op:
        batch_op.alter_column("title", type_=sa.Text(), existing_type=sa.String(length=255), nullable=False)
        batch_op.alter_column("title_kh", type_=sa.Text(), existing_type=sa.String(length=255), nullable=False)
        batch_op.alter_column("image_url", type_=sa.Text(), existing_type=sa.String(length=500), nullable=False)
        batch_op.alter_column("source_url", type_=sa.Text(), existing_type=sa.String(length=500), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("news_articles") as batch_op:
        batch_op.alter_column("title", type_=sa.String(length=255), existing_type=sa.Text(), nullable=False)
        batch_op.alter_column("title_kh", type_=sa.String(length=255), existing_type=sa.Text(), nullable=False)
        batch_op.alter_column("image_url", type_=sa.String(length=500), existing_type=sa.Text(), nullable=False)
        batch_op.alter_column("source_url", type_=sa.String(length=500), existing_type=sa.Text(), nullable=True)
