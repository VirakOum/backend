"""Create vehicle_models table and seed default popular vehicle models

Revision ID: 0029_vehicle_models
Revises: 0028_add_user_push_tokens
Create Date: 2026-08-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
from datetime import datetime

revision = "0029_vehicle_models"
down_revision = "0028_add_user_push_tokens"
branch_labels = None
depends_on = None

DEFAULT_CAR_MODELS = [
    {"brand": "Toyota", "model_name": "Prius", "display_name": "Toyota Prius", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 1},
    {"brand": "Toyota", "model_name": "Alphard", "display_name": "Toyota Alphard", "vehicle_type": "MPV / Minivan", "seat_count": 7, "sort_order": 2},
    {"brand": "Hyundai", "model_name": "Starex", "display_name": "Hyundai Starex", "vehicle_type": "Minivan", "seat_count": 12, "sort_order": 3},
    {"brand": "Lexus", "model_name": "RX330", "display_name": "Lexus RX330", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 4},
    {"brand": "Toyota", "model_name": "Sienna", "display_name": "Toyota Sienna", "vehicle_type": "Minivan", "seat_count": 7, "sort_order": 5},
    {"brand": "Ford", "model_name": "Everest", "display_name": "Ford Everest", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 6},
    {"brand": "Toyota", "model_name": "HiAce", "display_name": "Toyota HiAce", "vehicle_type": "Van", "seat_count": 15, "sort_order": 7},
    {"brand": "Toyota", "model_name": "Camry", "display_name": "Toyota Camry", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 8},
    {"brand": "Toyota", "model_name": "Fortuner", "display_name": "Toyota Fortuner", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 9},
    {"brand": "Hyundai", "model_name": "H1", "display_name": "Hyundai H1", "vehicle_type": "Van", "seat_count": 12, "sort_order": 10},
]

def upgrade() -> None:
    vehicle_models_table = op.create_table(
        "vehicle_models",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("brand", sa.String(length=50), nullable=False, index=True),
        sa.Column("model_name", sa.String(length=50), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("vehicle_type", sa.String(length=50), nullable=True),
        sa.Column("seat_count", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False, index=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_vehicle_models_active_sort", "vehicle_models", ["is_active", "sort_order"])

    # Bulk insert default popular car models
    now = datetime.utcnow()
    insert_data = [
        {
            "id": uuid.uuid4(),
            "brand": item["brand"],
            "model_name": item["model_name"],
            "display_name": item["display_name"],
            "vehicle_type": item["vehicle_type"],
            "seat_count": item["seat_count"],
            "is_active": True,
            "sort_order": item["sort_order"],
            "created_at": now,
            "updated_at": now,
        }
        for item in DEFAULT_CAR_MODELS
    ]
    op.bulk_insert(vehicle_models_table, insert_data)


def downgrade() -> None:
    op.drop_index("idx_vehicle_models_active_sort", table_name="vehicle_models")
    op.drop_table("vehicle_models")
