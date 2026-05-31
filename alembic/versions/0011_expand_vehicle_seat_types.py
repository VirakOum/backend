"""Expand vehicle seat types

Revision ID: 0011_expand_vehicle_seat_types
Revises: 0010_booking_payment_method
Create Date: 2026-05-28 00:00:00.000000

"""
from alembic import op


revision = "0011_expand_vehicle_seat_types"
down_revision = "0010_booking_payment_method"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("seat_type_check", "vehicles", type_="check")
    op.create_check_constraint(
        "seat_type_check",
        "vehicles",
        "seat_type IN (4, 15, 16, 23, 30, 45)",
    )


def downgrade() -> None:
    op.drop_constraint("seat_type_check", "vehicles", type_="check")
    op.create_check_constraint(
        "seat_type_check",
        "vehicles",
        "seat_type IN (4, 15, 30, 45)",
    )
