"""create items table

Revision ID: 0001_create_items_table
Revises:
Create Date: 2026-05-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0001_create_items_table"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=300), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("items")