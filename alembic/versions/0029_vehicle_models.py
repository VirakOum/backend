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
    # Toyota
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
    {"brand": "Toyota", "model_name": "Highlander", "display_name": "Toyota Highlander", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 11},
    {"brand": "Toyota", "model_name": "Land Cruiser", "display_name": "Toyota Land Cruiser", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 12},
    {"brand": "Toyota", "model_name": "Land Cruiser Prado", "display_name": "Toyota Land Cruiser Prado", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 13},
    {"brand": "Toyota", "model_name": "Corolla Cross", "display_name": "Toyota Corolla Cross", "vehicle_type": "Crossover", "seat_count": 4, "sort_order": 14},
    {"brand": "Toyota", "model_name": "Raize", "display_name": "Toyota Raize", "vehicle_type": "Compact SUV", "seat_count": 4, "sort_order": 15},
    {"brand": "Toyota", "model_name": "Hilux Revo", "display_name": "Toyota Hilux Revo", "vehicle_type": "Pickup", "seat_count": 4, "sort_order": 16},
    {"brand": "Toyota", "model_name": "Coaster", "display_name": "Toyota Coaster", "vehicle_type": "Minibus", "seat_count": 23, "sort_order": 17},
    {"brand": "Toyota", "model_name": "Veloz", "display_name": "Toyota Veloz", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 18},
    {"brand": "Toyota", "model_name": "Tacoma", "display_name": "Toyota Tacoma", "vehicle_type": "Pickup", "seat_count": 4, "sort_order": 19},

    # Lexus
    {"brand": "Lexus", "model_name": "NX300", "display_name": "Lexus NX300", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 20},
    {"brand": "Lexus", "model_name": "RX350", "display_name": "Lexus RX350", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 21},
    {"brand": "Lexus", "model_name": "LX570", "display_name": "Lexus LX570", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 22},
    {"brand": "Lexus", "model_name": "GX460", "display_name": "Lexus GX460", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 23},

    # Hyundai
    {"brand": "Hyundai", "model_name": "Staria", "display_name": "Hyundai Staria", "vehicle_type": "MPV / Minivan", "seat_count": 11, "sort_order": 24},
    {"brand": "Hyundai", "model_name": "Santa Fe", "display_name": "Hyundai Santa Fe", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 25},
    {"brand": "Hyundai", "model_name": "County", "display_name": "Hyundai County", "vehicle_type": "Bus", "seat_count": 25, "sort_order": 26},
    {"brand": "Hyundai", "model_name": "Solati", "display_name": "Hyundai Solati", "vehicle_type": "Minibus", "seat_count": 16, "sort_order": 27},
    {"brand": "Hyundai", "model_name": "Tucson", "display_name": "Hyundai Tucson", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 28},

    # Kia
    {"brand": "Kia", "model_name": "Carnival", "display_name": "Kia Carnival", "vehicle_type": "MPV / Minivan", "seat_count": 11, "sort_order": 29},
    {"brand": "Kia", "model_name": "Grand Carnival", "display_name": "Kia Grand Carnival", "vehicle_type": "MPV", "seat_count": 11, "sort_order": 30},
    {"brand": "Kia", "model_name": "Sorento", "display_name": "Kia Sorento", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 31},
    {"brand": "Kia", "model_name": "Morning", "display_name": "Kia Morning", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 32},

    # Ford
    {"brand": "Ford", "model_name": "Ranger Raptor", "display_name": "Ford Ranger Raptor", "vehicle_type": "Pickup", "seat_count": 4, "sort_order": 33},
    {"brand": "Ford", "model_name": "Transit", "display_name": "Ford Transit", "vehicle_type": "Van", "seat_count": 16, "sort_order": 34},
    {"brand": "Ford", "model_name": "Explorer", "display_name": "Ford Explorer", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 35},
    {"brand": "Ford", "model_name": "Territory", "display_name": "Ford Territory", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 36},

    # Mitsubishi
    {"brand": "Mitsubishi", "model_name": "Xpander", "display_name": "Mitsubishi Xpander", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 37},
    {"brand": "Mitsubishi", "model_name": "Pajero Sport", "display_name": "Mitsubishi Pajero Sport", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 38},
    {"brand": "Mitsubishi", "model_name": "Triton", "display_name": "Mitsubishi Triton", "vehicle_type": "Pickup", "seat_count": 4, "sort_order": 39},

    # Honda
    {"brand": "Honda", "model_name": "CR-V", "display_name": "Honda CR-V", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 40},
    {"brand": "Honda", "model_name": "HR-V", "display_name": "Honda HR-V", "vehicle_type": "Crossover", "seat_count": 4, "sort_order": 41},
    {"brand": "Honda", "model_name": "City", "display_name": "Honda City", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 42},

    # Nissan
    {"brand": "Nissan", "model_name": "Navara", "display_name": "Nissan Navara", "vehicle_type": "Pickup", "seat_count": 4, "sort_order": 43},
    {"brand": "Nissan", "model_name": "Urvan", "display_name": "Nissan Urvan", "vehicle_type": "Van", "seat_count": 15, "sort_order": 44},
    {"brand": "Nissan", "model_name": "Terra", "display_name": "Nissan Terra", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 45},

    # MG & BYD
    {"brand": "MG", "model_name": "ZS", "display_name": "MG ZS", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 46},
    {"brand": "BYD", "model_name": "Atto 3", "display_name": "BYD Atto 3", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 47},
    {"brand": "BYD", "model_name": "Dolphin", "display_name": "BYD Dolphin", "vehicle_type": "Electric Hatchback", "seat_count": 4, "sort_order": 48},
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
