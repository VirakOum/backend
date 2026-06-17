"""Separate trip live coordinates from departure coordinates

Revision ID: 0024_separate_trip_live_coordinates
Revises: 0023_add_boarding_confirmation_and_passenger_live_location
Create Date: 2026-06-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0024_separate_trip_live_coordinates"
down_revision = "0023_add_boarding_confirmation_and_passenger_live_location"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trips", sa.Column("live_lat", sa.Numeric(10, 6), nullable=True))
    op.add_column("trips", sa.Column("live_lng", sa.Numeric(10, 6), nullable=True))

    op.execute(
        """
        UPDATE trips
        SET live_lat = departure_lat,
            live_lng = departure_lng
        WHERE live_location_expires_at IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_column("trips", "live_lng")
    op.drop_column("trips", "live_lat")
