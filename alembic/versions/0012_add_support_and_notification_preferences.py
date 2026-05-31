"""Add support tickets and notification preferences

Revision ID: 0012_support_notifications
Revises: 0011_expand_vehicle_seat_types
Create Date: 2026-05-31 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0012_support_notifications"
down_revision = "0011_expand_vehicle_seat_types"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("booking_updates", sa.Boolean(), nullable=False),
        sa.Column("route_promotions", sa.Boolean(), nullable=False),
        sa.Column("pickup_reminders", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_table(
        "support_tickets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("passenger_location", sa.JSON(), nullable=True),
        sa.Column("driver_location", sa.JSON(), nullable=True),
        sa.Column("locale", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "status IN ('open', 'in_progress', 'resolved', 'closed')",
            name="support_ticket_status_check",
        ),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_support_tickets_booking_id"), "support_tickets", ["booking_id"], unique=False)
    op.create_index(op.f("ix_support_tickets_trip_id"), "support_tickets", ["trip_id"], unique=False)
    op.create_index(op.f("ix_support_tickets_user_id"), "support_tickets", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_support_tickets_user_id"), table_name="support_tickets")
    op.drop_index(op.f("ix_support_tickets_trip_id"), table_name="support_tickets")
    op.drop_index(op.f("ix_support_tickets_booking_id"), table_name="support_tickets")
    op.drop_table("support_tickets")
    op.drop_table("notification_preferences")
