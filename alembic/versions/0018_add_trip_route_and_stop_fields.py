"""Add structured trip route and stop fields

Revision ID: 0018_trip_route_stop_fields
Revises: 0017_address_form_entries
Create Date: 2026-06-05 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0018_trip_route_stop_fields"
down_revision = "0017_address_form_entries"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trips", sa.Column("departure_route", sa.JSON(), nullable=True))
    op.add_column("trips", sa.Column("destination_route", sa.JSON(), nullable=True))
    op.add_column("trips", sa.Column("pickup_stop", sa.JSON(), nullable=True))
    op.add_column("trips", sa.Column("dropoff_stop", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("trips", "dropoff_stop")
    op.drop_column("trips", "pickup_stop")
    op.drop_column("trips", "destination_route")
    op.drop_column("trips", "departure_route")
