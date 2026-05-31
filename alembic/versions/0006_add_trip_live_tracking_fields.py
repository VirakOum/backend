"""Add trip live tracking fields

Revision ID: 0006_trip_live_tracking
Revises: 0005_trip_live_weekly
Create Date: 2026-05-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0006_trip_live_tracking"
down_revision = "0005_trip_live_weekly"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trips", sa.Column("live_heading", sa.Integer(), nullable=True))
    op.add_column("trips", sa.Column("live_speed_kph", sa.Numeric(6, 2), nullable=True))
    op.add_column("trips", sa.Column("live_location_updated_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("trips", "live_location_updated_at")
    op.drop_column("trips", "live_speed_kph")
    op.drop_column("trips", "live_heading")
