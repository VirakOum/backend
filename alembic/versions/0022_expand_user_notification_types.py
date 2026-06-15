"""Expand user notification types

Revision ID: 0022_expand_user_notification_types
Revises: 0021_add_user_notifications
Create Date: 2026-06-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0022_expand_user_notification_types"
down_revision = "0021_add_user_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "user_notification_type_check",
        "user_notifications",
        type_="check",
    )
    op.create_check_constraint(
        "user_notification_type_check",
        "user_notifications",
        "type IN ('driver_arrived', 'booking_created')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "user_notification_type_check",
        "user_notifications",
        type_="check",
    )
    op.create_check_constraint(
        "user_notification_type_check",
        "user_notifications",
        "type IN ('driver_arrived')",
    )
