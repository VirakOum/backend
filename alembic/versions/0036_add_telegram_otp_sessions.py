"""Add telegram_otp_sessions table for Telegram Bot OTP verification

Revision ID: 0036_add_telegram_otp_sessions
Revises: 0035_add_universal_link_configs
Create Date: 2026-10-27 14:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0036_add_telegram_otp_sessions"
down_revision = "0035_add_universal_link_configs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "telegram_otp_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_token", sa.String(length=64), nullable=False, unique=True),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("purpose", sa.String(length=30), nullable=False, server_default="login"),
        sa.Column("otp_code", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("telegram_chat_id", sa.String(length=64), nullable=True),
        sa.Column("telegram_username", sa.String(length=100), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_telegram_otp_sessions_session_token", "telegram_otp_sessions", ["session_token"])
    op.create_index("ix_telegram_otp_sessions_phone", "telegram_otp_sessions", ["phone"])
    op.create_index("ix_telegram_otp_sessions_status", "telegram_otp_sessions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_telegram_otp_sessions_status", table_name="telegram_otp_sessions")
    op.drop_index("ix_telegram_otp_sessions_phone", table_name="telegram_otp_sessions")
    op.drop_index("ix_telegram_otp_sessions_session_token", table_name="telegram_otp_sessions")
    op.drop_table("telegram_otp_sessions")
