"""Add booking arrival and payment instruction state

Revision ID: 0013_booking_arrival_payment
Revises: 0012_support_notifications
Create Date: 2026-06-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0013_booking_arrival_payment"
down_revision = "0012_support_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bookings", sa.Column("payment_status", sa.String(length=20), server_default="pending", nullable=False))
    op.add_column("bookings", sa.Column("pickup_status", sa.String(length=30), server_default="pending", nullable=False))
    op.add_column("bookings", sa.Column("driver_arrived_at", sa.DateTime(), nullable=True))
    op.create_check_constraint(
        "booking_payment_status_check",
        "bookings",
        "payment_status IN ('pending', 'opened', 'paid', 'failed', 'cancelled')",
    )
    op.create_check_constraint(
        "booking_pickup_status_check",
        "bookings",
        "pickup_status IN ('pending', 'driver_arrived', 'passenger_boarded', 'completed')",
    )
    op.alter_column("bookings", "payment_status", server_default=None)
    op.alter_column("bookings", "pickup_status", server_default=None)

    op.create_table(
        "booking_payment_instructions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_type", sa.String(length=30), nullable=False),
        sa.Column("deep_link_url", sa.Text(), nullable=True),
        sa.Column("qr_image_url", sa.Text(), nullable=True),
        sa.Column("qr_payload", sa.Text(), nullable=True),
        sa.Column("raw_message", sa.Text(), nullable=True),
        sa.Column("parse_status", sa.String(length=30), nullable=False),
        sa.Column("bank_provider", sa.String(length=50), nullable=True),
        sa.Column("payment_status", sa.String(length=20), nullable=False),
        sa.Column("captured_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "payment_status IN ('pending', 'opened', 'paid', 'failed', 'cancelled')",
            name="booking_payment_instruction_payment_status_check",
        ),
        sa.CheckConstraint(
            "parse_status IN ('missing', 'parsed', 'manual', 'image_stored', 'invalid')",
            name="booking_payment_instruction_parse_status_check",
        ),
        sa.CheckConstraint(
            "source_type IN ('none', 'text', 'manual', 'qr_image', 'qr_payload')",
            name="booking_payment_instruction_source_type_check",
        ),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("booking_id"),
    )
    op.create_index(op.f("ix_booking_payment_instructions_booking_id"), "booking_payment_instructions", ["booking_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_booking_payment_instructions_booking_id"), table_name="booking_payment_instructions")
    op.drop_table("booking_payment_instructions")
    op.drop_constraint("booking_pickup_status_check", "bookings", type_="check")
    op.drop_constraint("booking_payment_status_check", "bookings", type_="check")
    op.drop_column("bookings", "driver_arrived_at")
    op.drop_column("bookings", "pickup_status")
    op.drop_column("bookings", "payment_status")
