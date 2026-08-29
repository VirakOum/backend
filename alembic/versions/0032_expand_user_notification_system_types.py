"""Expand user notification types for system messages and announcements

Revision ID: 0032_expand_user_notification_system_types
Revises: 0031_add_news_articles
Create Date: 2026-08-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0032_expand_user_notification_system_types'
down_revision = '0031_add_news_articles'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("user_notification_type_check", "user_notifications", type_="check")
    op.create_check_constraint(
        "user_notification_type_check",
        "user_notifications",
        "type IN ('driver_arrived', 'booking_created', 'boarding_requested', 'boarding_confirmed', 'system_announcement', 'system_info')",
    )


def downgrade() -> None:
    op.drop_constraint("user_notification_type_check", "user_notifications", type_="check")
    op.create_check_constraint(
        "user_notification_type_check",
        "user_notifications",
        "type IN ('driver_arrived', 'booking_created', 'boarding_requested', 'boarding_confirmed')",
    )
