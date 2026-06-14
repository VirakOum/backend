"""Add user notifications table

Revision ID: 0021_add_user_notifications
Revises: 0020_cash_driver_debt_flow
Create Date: 2026-06-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0021_add_user_notifications"
down_revision = "0020_cash_driver_debt_flow"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("type IN ('driver_arrived')", name="user_notification_type_check"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_notifications_user_id", "user_notifications", ["user_id"], unique=False)
    op.create_index("ix_user_notifications_trip_id", "user_notifications", ["trip_id"], unique=False)
    op.create_index("ix_user_notifications_booking_id", "user_notifications", ["booking_id"], unique=False)
    op.create_index("ix_user_notifications_is_read", "user_notifications", ["is_read"], unique=False)
    op.create_index("ix_user_notifications_created_at", "user_notifications", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_user_notifications_created_at", table_name="user_notifications")
    op.drop_index("ix_user_notifications_is_read", table_name="user_notifications")
    op.drop_index("ix_user_notifications_booking_id", table_name="user_notifications")
    op.drop_index("ix_user_notifications_trip_id", table_name="user_notifications")
    op.drop_index("ix_user_notifications_user_id", table_name="user_notifications")
    op.drop_table("user_notifications")
