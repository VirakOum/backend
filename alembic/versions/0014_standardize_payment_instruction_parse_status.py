"""Standardize payment instruction parse status

Revision ID: 0014_payment_parse_status
Revises: 0013_booking_arrival_payment
Create Date: 2026-06-01 00:00:00.000000

"""
from alembic import op


revision = "0014_payment_parse_status"
down_revision = "0013_booking_arrival_payment"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "booking_payment_instruction_parse_status_check",
        "booking_payment_instructions",
        type_="check",
    )
    op.execute(
        """
        UPDATE booking_payment_instructions
        SET parse_status = CASE
            WHEN deep_link_url IS NOT NULL OR qr_payload IS NOT NULL THEN 'parsed'
            WHEN qr_image_url IS NOT NULL OR raw_message IS NOT NULL THEN 'failed'
            ELSE 'missing'
        END
        """
    )
    op.create_check_constraint(
        "booking_payment_instruction_parse_status_check",
        "booking_payment_instructions",
        "parse_status IN ('missing', 'parsed', 'failed')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "booking_payment_instruction_parse_status_check",
        "booking_payment_instructions",
        type_="check",
    )
    op.create_check_constraint(
        "booking_payment_instruction_parse_status_check",
        "booking_payment_instructions",
        "parse_status IN ('missing', 'parsed', 'manual', 'image_stored', 'invalid')",
    )
