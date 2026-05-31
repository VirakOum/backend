"""Add booking payment method

Revision ID: 0010_booking_payment_method
Revises: 0009_phnom_penh_timestamps
Create Date: 2026-05-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0010_booking_payment_method"
down_revision = "0009_phnom_penh_timestamps"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "bookings",
        sa.Column("payment_method", sa.String(length=20), nullable=False, server_default="cash_on_arrival"),
    )
    op.create_check_constraint(
        "booking_payment_method_check",
        "bookings",
        "payment_method IN ('khqr', 'cash_on_arrival')",
    )


def downgrade() -> None:
    op.drop_constraint("booking_payment_method_check", "bookings", type_="check")
    op.drop_column("bookings", "payment_method")
