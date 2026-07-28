"""Add system_messages table for admin message broadcasts

Revision ID: 0027_add_system_messages
Revises: 67daf2cb89a5
Create Date: 2026-07-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0027_add_system_messages"
down_revision = "67daf2cb89a5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "system_messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("target_role", sa.String(length=20), nullable=False, server_default="all"),
        sa.Column("message_type", sa.String(length=30), nullable=False, server_default="info"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("broadcast_to_notifications", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "target_role IN ('all', 'driver', 'passenger')",
            name="system_message_target_role_check",
        ),
        sa.CheckConstraint(
            "message_type IN ('info', 'warning', 'announcement', 'maintenance')",
            name="system_message_type_check",
        ),
    )
    op.create_index("ix_system_messages_target_role", "system_messages", ["target_role"])
    op.create_index("ix_system_messages_message_type", "system_messages", ["message_type"])
    op.create_index("ix_system_messages_is_active", "system_messages", ["is_active"])
    op.create_index("ix_system_messages_is_pinned", "system_messages", ["is_pinned"])
    op.create_index("ix_system_messages_created_at", "system_messages", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_system_messages_created_at", table_name="system_messages")
    op.drop_index("ix_system_messages_is_pinned", table_name="system_messages")
    op.drop_index("ix_system_messages_is_active", table_name="system_messages")
    op.drop_index("ix_system_messages_message_type", table_name="system_messages")
    op.drop_index("ix_system_messages_target_role", table_name="system_messages")
    op.drop_table("system_messages")
