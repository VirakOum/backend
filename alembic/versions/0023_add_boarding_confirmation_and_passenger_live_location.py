"""Add boarding confirmation columns and passenger live location table

Revision ID: 0023_add_boarding_confirmation_and_passenger_live_location
Revises: 0022_expand_user_notification_types
Create Date: 2026-06-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0023_add_boarding_confirmation_and_passenger_live_location"
down_revision = "0022_expand_user_notification_types"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add boarding confirmation columns to bookings
    op.add_column("bookings", sa.Column("driver_requested_boarding_at", sa.DateTime(), nullable=True))
    op.add_column("bookings", sa.Column("passenger_confirmed_boarding_at", sa.DateTime(), nullable=True))
    op.add_column("bookings", sa.Column("boarding_confirmation_expires_at", sa.DateTime(), nullable=True))

    # Create passenger live locations table
    op.create_table(
        "booking_live_locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, unique=True, index=True),
        sa.Column("lat", sa.Numeric(10, 6), nullable=False),
        sa.Column("lng", sa.Numeric(10, 6), nullable=False),
        sa.Column("accuracy_m", sa.Numeric(10, 2), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
    )

    # Update user_notification type check constraint
    op.drop_constraint("user_notification_type_check", "user_notifications", type_="check")
    op.create_check_constraint(
        "user_notification_type_check",
        "user_notifications",
        "type IN ('driver_arrived', 'booking_created', 'boarding_requested', 'boarding_confirmed')",
    )


def downgrade() -> None:
    op.drop_table("booking_live_locations")
    op.drop_column("bookings", "boarding_confirmation_expires_at")
    op.drop_column("bookings", "passenger_confirmed_boarding_at")
    op.drop_column("bookings", "driver_requested_boarding_at")

    op.drop_constraint("user_notification_type_check", "user_notifications", type_="check")
    op.create_check_constraint(
        "user_notification_type_check",
        "user_notifications",
        "type IN ('driver_arrived', 'booking_created')",
    )
