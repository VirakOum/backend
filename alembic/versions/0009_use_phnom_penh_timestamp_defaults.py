"""Use Phnom Penh timestamp defaults

Revision ID: 0009_phnom_penh_timestamps
Revises: 0008_trip_detail_fields
Create Date: 2026-05-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0009_phnom_penh_timestamps"
down_revision = "0008_trip_detail_fields"
branch_labels = None
depends_on = None


LOCAL_NOW = sa.text("timezone('Asia/Phnom_Penh', now())")


def upgrade() -> None:
    for table_name in (
        "users",
        "vehicles",
        "trips",
        "bookings",
        "payments",
        "auth_tokens",
        "passenger_quick_places",
    ):
        op.alter_column(table_name, "created_at", server_default=LOCAL_NOW)
    op.alter_column("passenger_quick_places", "updated_at", server_default=LOCAL_NOW)


def downgrade() -> None:
    for table_name in (
        "users",
        "vehicles",
        "trips",
        "bookings",
        "payments",
        "auth_tokens",
        "passenger_quick_places",
    ):
        op.alter_column(table_name, "created_at", server_default=sa.func.now())
    op.alter_column("passenger_quick_places", "updated_at", server_default=sa.func.now())
