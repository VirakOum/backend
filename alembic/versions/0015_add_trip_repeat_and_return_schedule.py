"""Add trip repeat and return schedule fields

Revision ID: 0015_trip_repeat_return
Revises: 0014_payment_parse_status
Create Date: 2026-06-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0015_trip_repeat_return"
down_revision = "0014_payment_parse_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trips", sa.Column("repeat_mode", sa.String(length=20), server_default="none", nullable=False))
    op.add_column("trips", sa.Column("has_return_schedule", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column("trips", sa.Column("return_departure_time", sa.DateTime(), nullable=True))
    op.add_column("trips", sa.Column("return_trip_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_check_constraint(
        "trip_repeat_mode_check",
        "trips",
        "repeat_mode IN ('none', 'daily', 'weekly')",
    )
    op.create_foreign_key(
        "fk_trips_return_trip_id_trips",
        "trips",
        "trips",
        ["return_trip_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.execute("UPDATE trips SET repeat_mode = 'weekly' WHERE auto_repeat_weekly = true")
    op.alter_column("trips", "repeat_mode", server_default=None)
    op.alter_column("trips", "has_return_schedule", server_default=None)


def downgrade() -> None:
    op.drop_constraint("fk_trips_return_trip_id_trips", "trips", type_="foreignkey")
    op.drop_constraint("trip_repeat_mode_check", "trips", type_="check")
    op.drop_column("trips", "return_trip_id")
    op.drop_column("trips", "return_departure_time")
    op.drop_column("trips", "has_return_schedule")
    op.drop_column("trips", "repeat_mode")
