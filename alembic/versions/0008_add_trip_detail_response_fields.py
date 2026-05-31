"""Add trip detail response fields

Revision ID: 0008_trip_detail_fields
Revises: 0007_trip_route_idx
Create Date: 2026-05-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0008_trip_detail_fields"
down_revision = "0007_trip_route_idx"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("rating_avg", sa.Numeric(3, 2), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("rating_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("completed_trips", sa.Integer(), nullable=False, server_default="0"))

    op.add_column("vehicles", sa.Column("vehicle_type", sa.String(length=50), nullable=True))
    op.add_column("vehicles", sa.Column("color", sa.String(length=30), nullable=True))

    op.add_column("trips", sa.Column("promotion_label", sa.String(length=50), nullable=True))
    op.add_column("trips", sa.Column("promotion_discount_percent", sa.Integer(), nullable=True))
    op.create_check_constraint(
        "trip_promotion_discount_percent_check",
        "trips",
        "promotion_discount_percent IS NULL OR (promotion_discount_percent >= 0 AND promotion_discount_percent <= 100)",
    )


def downgrade() -> None:
    op.drop_constraint("trip_promotion_discount_percent_check", "trips", type_="check")
    op.drop_column("trips", "promotion_discount_percent")
    op.drop_column("trips", "promotion_label")

    op.drop_column("vehicles", "color")
    op.drop_column("vehicles", "vehicle_type")

    op.drop_column("users", "completed_trips")
    op.drop_column("users", "rating_count")
    op.drop_column("users", "rating_avg")
