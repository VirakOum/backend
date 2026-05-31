"""Add trip live location and weekly repeat fields

Revision ID: 0005_trip_live_weekly
Revises: 0004_passenger_quick_places
Create Date: 2026-05-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0005_trip_live_weekly"
down_revision = "0004_passenger_quick_places"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trips", sa.Column("departure_lat", sa.Numeric(10, 6), nullable=True))
    op.add_column("trips", sa.Column("departure_lng", sa.Numeric(10, 6), nullable=True))
    op.add_column("trips", sa.Column("live_location_expires_at", sa.DateTime(), nullable=True))
    op.add_column(
        "trips",
        sa.Column("auto_repeat_weekly", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column("trips", sa.Column("recurring_day_of_week", sa.Integer(), nullable=True))
    op.add_column("trips", sa.Column("recurring_departure_time", sa.Time(), nullable=True))
    op.create_check_constraint(
        "trip_recurring_day_of_week_check",
        "trips",
        "recurring_day_of_week IS NULL OR (recurring_day_of_week >= 0 AND recurring_day_of_week <= 6)",
    )


def downgrade() -> None:
    op.drop_constraint("trip_recurring_day_of_week_check", "trips", type_="check")
    op.drop_column("trips", "recurring_departure_time")
    op.drop_column("trips", "recurring_day_of_week")
    op.drop_column("trips", "auto_repeat_weekly")
    op.drop_column("trips", "live_location_expires_at")
    op.drop_column("trips", "departure_lng")
    op.drop_column("trips", "departure_lat")
