"""Add vehicle images and flexible seat count

Revision ID: 0026_vehicle_images_and_flexible_seat_count
Revises: 0025_add_trusted_devices
Create Date: 2026-07-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0026_vehicle_images_and_flexible_seat_count"
down_revision = "0025_add_trusted_devices"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("vehicles", sa.Column("image_urls", sa.JSON(), nullable=True))
    op.drop_constraint("seat_type_check", "vehicles", type_="check")
    op.create_check_constraint(
        "seat_type_check",
        "vehicles",
        "seat_type > 0",
    )


def downgrade() -> None:
    op.drop_constraint("seat_type_check", "vehicles", type_="check")
    op.create_check_constraint(
        "seat_type_check",
        "vehicles",
        "seat_type IN (4, 15, 16, 23, 30, 45)",
    )
    op.drop_column("vehicles", "image_urls")
