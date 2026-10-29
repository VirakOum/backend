"""Add is_active column to users table

Revision ID: 0037_add_is_active_to_users
Revises: 0036_add_telegram_otp_sessions
Create Date: 2026-10-29 14:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0037_add_is_active_to_users"
down_revision = "0036_add_telegram_otp_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.create_index("ix_users_is_active", "users", ["is_active"])


def downgrade() -> None:
    op.drop_index("ix_users_is_active", table_name="users")
    op.drop_column("users", "is_active")

