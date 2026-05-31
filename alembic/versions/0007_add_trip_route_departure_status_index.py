"""Add trip route+departure+status index

Revision ID: 0007_trip_route_idx
Revises: 0006_trip_live_tracking
Create Date: 2026-05-26 00:00:00.000000

"""
from alembic import op


revision = "0007_trip_route_idx"
down_revision = "0006_trip_live_tracking"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_trips_route_departure_status",
        "trips",
        ["departure_province", "destination_province", "departure_time", "status"],
    )


def downgrade() -> None:
    op.drop_index("idx_trips_route_departure_status", table_name="trips")
