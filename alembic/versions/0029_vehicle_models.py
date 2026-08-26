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
    {'brand': 'Toyota', 'model_name': 'Prius', 'display_name': 'Toyota Prius', 'vehicle_type': 'Sedan', 'seat_count': 4, 'sort_order': 1},
    {'brand': 'Toyota', 'model_name': 'Alphard', 'display_name': 'Toyota Alphard', 'vehicle_type': 'MPV / Minivan', 'seat_count': 7, 'sort_order': 2},
    {'brand': 'Hyundai', 'model_name': 'Starex', 'display_name': 'Hyundai Starex', 'vehicle_type': 'Minivan', 'seat_count': 12, 'sort_order': 3},
    {'brand': 'Lexus', 'model_name': 'RX330', 'display_name': 'Lexus RX330', 'vehicle_type': 'SUV', 'seat_count': 4, 'sort_order': 4},
    {'brand': 'Toyota', 'model_name': 'Sienna', 'display_name': 'Toyota Sienna', 'vehicle_type': 'Minivan', 'seat_count': 7, 'sort_order': 5},
    {'brand': 'Ford', 'model_name': 'Everest', 'display_name': 'Ford Everest', 'vehicle_type': 'SUV', 'seat_count': 7, 'sort_order': 6},
    {'brand': 'Toyota', 'model_name': 'HiAce', 'display_name': 'Toyota HiAce', 'vehicle_type': 'Van', 'seat_count': 15, 'sort_order': 7},
    {'brand': 'Toyota', 'model_name': 'Camry', 'display_name': 'Toyota Camry', 'vehicle_type': 'Sedan', 'seat_count': 4, 'sort_order': 8},
    {'brand': 'Toyota', 'model_name': 'Fortuner', 'display_name': 'Toyota Fortuner', 'vehicle_type': 'SUV', 'seat_count': 7, 'sort_order': 9},
    {'brand': 'Hyundai', 'model_name': 'H1', 'display_name': 'Hyundai H1', 'vehicle_type': 'Van', 'seat_count': 12, 'sort_order': 10},
    {'brand': 'Toyota', 'model_name': 'Highlander', 'display_name': 'Toyota Highlander', 'vehicle_type': 'SUV', 'seat_count': 7, 'sort_order': 11},
    {'brand': 'Toyota', 'model_name': 'Land Cruiser', 'display_name': 'Toyota Land Cruiser', 'vehicle_type': 'SUV', 'seat_count': 7, 'sort_order': 12},
    {'brand': 'Toyota', 'model_name': 'Land Cruiser Prado', 'display_name': 'Toyota Land Cruiser Prado', 'vehicle_type': 'SUV', 'seat_count': 7, 'sort_order': 13},
    {'brand': 'Toyota', 'model_name': 'Corolla Cross', 'display_name': 'Toyota Corolla Cross', 'vehicle_type': 'Crossover', 'seat_count': 4, 'sort_order': 14},
    {'brand': 'Toyota', 'model_name': 'Raize', 'display_name': 'Toyota Raize', 'vehicle_type': 'Compact SUV', 'seat_count': 4, 'sort_order': 15},
    {'brand': 'Toyota', 'model_name': 'Hilux Revo', 'display_name': 'Toyota Hilux Revo', 'vehicle_type': 'Pickup', 'seat_count': 4, 'sort_order': 16},
    {'brand': 'Toyota', 'model_name': 'Coaster', 'display_name': 'Toyota Coaster', 'vehicle_type': 'Minibus', 'seat_count': 23, 'sort_order': 17},
    {'brand': 'Toyota', 'model_name': 'Veloz', 'display_name': 'Toyota Veloz', 'vehicle_type': 'MPV', 'seat_count': 7, 'sort_order': 18},
    {'brand': 'Toyota', 'model_name': 'Tacoma', 'display_name': 'Toyota Tacoma', 'vehicle_type': 'Pickup', 'seat_count': 4, 'sort_order': 19},
    {'brand': 'Lexus', 'model_name': 'NX300', 'display_name': 'Lexus NX300', 'vehicle_type': 'SUV', 'seat_count': 4, 'sort_order': 20},
    {'brand': 'Lexus', 'model_name': 'RX350', 'display_name': 'Lexus RX350', 'vehicle_type': 'SUV', 'seat_count': 4, 'sort_order': 21},
    {'brand': 'Lexus', 'model_name': 'LX570', 'display_name': 'Lexus LX570', 'vehicle_type': 'SUV', 'seat_count': 7, 'sort_order': 22},
    {'brand': 'Lexus', 'model_name': 'GX460', 'display_name': 'Lexus GX460', 'vehicle_type': 'SUV', 'seat_count': 7, 'sort_order': 23},
    {'brand': 'Hyundai', 'model_name': 'Staria', 'display_name': 'Hyundai Staria', 'vehicle_type': 'MPV / Minivan', 'seat_count': 11, 'sort_order': 24},
    {'brand': 'Hyundai', 'model_name': 'Santa Fe', 'display_name': 'Hyundai Santa Fe', 'vehicle_type': 'SUV', 'seat_count': 7, 'sort_order': 25},
    {'brand': 'Hyundai', 'model_name': 'County', 'display_name': 'Hyundai County', 'vehicle_type': 'Bus', 'seat_count': 25, 'sort_order': 26},
    {'brand': 'Hyundai', 'model_name': 'Solati', 'display_name': 'Hyundai Solati', 'vehicle_type': 'Minibus', 'seat_count': 16, 'sort_order': 27},
    {'brand': 'Hyundai', 'model_name': 'Tucson', 'display_name': 'Hyundai Tucson', 'vehicle_type': 'SUV', 'seat_count': 4, 'sort_order': 28},
    {'brand': 'Kia', 'model_name': 'Carnival', 'display_name': 'Kia Carnival', 'vehicle_type': 'MPV / Minivan', 'seat_count': 11, 'sort_order': 29},
    {'brand': 'Kia', 'model_name': 'Grand Carnival', 'display_name': 'Kia Grand Carnival', 'vehicle_type': 'MPV', 'seat_count': 11, 'sort_order': 30},
    {'brand': 'Kia', 'model_name': 'Sorento', 'display_name': 'Kia Sorento', 'vehicle_type': 'SUV', 'seat_count': 7, 'sort_order': 31},
    {'brand': 'Kia', 'model_name': 'Morning', 'display_name': 'Kia Morning', 'vehicle_type': 'Hatchback', 'seat_count': 4, 'sort_order': 32},
    {'brand': 'Ford', 'model_name': 'Ranger Raptor', 'display_name': 'Ford Ranger Raptor', 'vehicle_type': 'Pickup', 'seat_count': 4, 'sort_order': 33},
    {'brand': 'Ford', 'model_name': 'Transit', 'display_name': 'Ford Transit', 'vehicle_type': 'Van', 'seat_count': 16, 'sort_order': 34},
    {'brand': 'Ford', 'model_name': 'Explorer', 'display_name': 'Ford Explorer', 'vehicle_type': 'SUV', 'seat_count': 7, 'sort_order': 35},
    {'brand': 'Ford', 'model_name': 'Territory', 'display_name': 'Ford Territory', 'vehicle_type': 'SUV', 'seat_count': 4, 'sort_order': 36},
    {'brand': 'Mitsubishi', 'model_name': 'Xpander', 'display_name': 'Mitsubishi Xpander', 'vehicle_type': 'MPV', 'seat_count': 7, 'sort_order': 37},
    {'brand': 'Mitsubishi', 'model_name': 'Pajero Sport', 'display_name': 'Mitsubishi Pajero Sport', 'vehicle_type': 'SUV', 'seat_count': 7, 'sort_order': 38},
    {'brand': 'Mitsubishi', 'model_name': 'Triton', 'display_name': 'Mitsubishi Triton', 'vehicle_type': 'Pickup', 'seat_count': 4, 'sort_order': 39},
    {'brand': 'Honda', 'model_name': 'CR-V', 'display_name': 'Honda CR-V', 'vehicle_type': 'SUV', 'seat_count': 4, 'sort_order': 40},
    {'brand': 'Honda', 'model_name': 'HR-V', 'display_name': 'Honda HR-V', 'vehicle_type': 'Crossover', 'seat_count': 4, 'sort_order': 41},
    {'brand': 'Honda', 'model_name': 'City', 'display_name': 'Honda City', 'vehicle_type': 'Sedan', 'seat_count': 4, 'sort_order': 42},
    {'brand': 'Nissan', 'model_name': 'Navara', 'display_name': 'Nissan Navara', 'vehicle_type': 'Pickup', 'seat_count': 4, 'sort_order': 43},
    {'brand': 'Nissan', 'model_name': 'Urvan', 'display_name': 'Nissan Urvan', 'vehicle_type': 'Van', 'seat_count': 15, 'sort_order': 44},
    {'brand': 'Nissan', 'model_name': 'Terra', 'display_name': 'Nissan Terra', 'vehicle_type': 'SUV', 'seat_count': 7, 'sort_order': 45},
    {'brand': 'MG', 'model_name': 'ZS', 'display_name': 'MG ZS', 'vehicle_type': 'SUV', 'seat_count': 4, 'sort_order': 46},
    {'brand': 'BYD', 'model_name': 'Atto 3', 'display_name': 'BYD Atto 3', 'vehicle_type': 'Electric SUV', 'seat_count': 4, 'sort_order': 47},
    {'brand': 'BYD', 'model_name': 'Dolphin', 'display_name': 'BYD Dolphin', 'vehicle_type': 'Electric Hatchback', 'seat_count': 4, 'sort_order': 48},
    {'brand': 'Toyota', 'model_name': 'Vios', 'display_name': 'Toyota Vios', 'vehicle_type': 'Sedan', 'seat_count': 4, 'sort_order': 49},
    {'brand': 'Toyota', 'model_name': 'Innova', 'display_name': 'Toyota Innova', 'vehicle_type': 'MPV', 'seat_count': 7, 'sort_order': 50},
    {'brand': 'Toyota', 'model_name': 'Avanza', 'display_name': 'Toyota Avanza', 'vehicle_type': 'MPV', 'seat_count': 7, 'sort_order': 51},
    {'brand': 'Toyota', 'model_name': 'Yaris Cross', 'display_name': 'Toyota Yaris Cross', 'vehicle_type': 'Crossover', 'seat_count': 4, 'sort_order': 52},
    {'brand': 'Toyota', 'model_name': 'Vellfire', 'display_name': 'Toyota Vellfire', 'vehicle_type': 'Luxury MPV', 'seat_count': 7, 'sort_order': 53},
    {'brand': 'Toyota', 'model_name': 'Crown', 'display_name': 'Toyota Crown', 'vehicle_type': 'Luxury Sedan', 'seat_count': 4, 'sort_order': 54},
    {'brand': 'Toyota', 'model_name': 'Granvia', 'display_name': 'Toyota Granvia', 'vehicle_type': 'VIP Van', 'seat_count': 9, 'sort_order': 55},
    {'brand': 'Toyota', 'model_name': '4Runner', 'display_name': 'Toyota 4Runner', 'vehicle_type': 'SUV', 'seat_count': 7, 'sort_order': 56},
    {'brand': 'Toyota', 'model_name': 'bZ4X', 'display_name': 'Toyota bZ4X', 'vehicle_type': 'Electric SUV', 'seat_count': 4, 'sort_order': 57},
    {'brand': 'Lexus', 'model_name': 'ES300h', 'display_name': 'Lexus ES300h', 'vehicle_type': 'Luxury Hybrid Sedan', 'seat_count': 4, 'sort_order': 58},
    {'brand': 'Lexus', 'model_name': 'LM350h', 'display_name': 'Lexus LM350h', 'vehicle_type': 'Luxury MPV', 'seat_count': 7, 'sort_order': 59},
    {'brand': 'Lexus', 'model_name': 'LX600', 'display_name': 'Lexus LX600', 'vehicle_type': 'Luxury SUV', 'seat_count': 7, 'sort_order': 60},
    {'brand': 'Lexus', 'model_name': 'IS250', 'display_name': 'Lexus IS250', 'vehicle_type': 'Sedan', 'seat_count': 4, 'sort_order': 61},
    {'brand': 'Lexus', 'model_name': 'RX450h', 'display_name': 'Lexus RX450h', 'vehicle_type': 'Hybrid SUV', 'seat_count': 4, 'sort_order': 62},
    {'brand': 'Hyundai', 'model_name': 'Elantra', 'display_name': 'Hyundai Elantra', 'vehicle_type': 'Sedan', 'seat_count': 4, 'sort_order': 63},
    {'brand': 'Hyundai', 'model_name': 'Accent', 'display_name': 'Hyundai Accent', 'vehicle_type': 'Sedan', 'seat_count': 4, 'sort_order': 64},
    {'brand': 'Hyundai', 'model_name': 'Ioniq 5', 'display_name': 'Hyundai Ioniq 5', 'vehicle_type': 'Electric SUV', 'seat_count': 4, 'sort_order': 65},
    {'brand': 'Hyundai', 'model_name': 'Kona', 'display_name': 'Hyundai Kona', 'vehicle_type': 'Compact SUV', 'seat_count': 4, 'sort_order': 66},
    {'brand': 'Kia', 'model_name': 'Seltos', 'display_name': 'Kia Seltos', 'vehicle_type': 'Compact SUV', 'seat_count': 4, 'sort_order': 67},
    {'brand': 'Kia', 'model_name': 'K5', 'display_name': 'Kia K5', 'vehicle_type': 'Sedan', 'seat_count': 4, 'sort_order': 68},
    {'brand': 'Kia', 'model_name': 'EV6', 'display_name': 'Kia EV6', 'vehicle_type': 'Electric SUV', 'seat_count': 4, 'sort_order': 69},
    {'brand': 'Kia', 'model_name': 'Soluto', 'display_name': 'Kia Soluto', 'vehicle_type': 'Sedan', 'seat_count': 4, 'sort_order': 70},
    {'brand': 'Ford', 'model_name': 'Ranger', 'display_name': 'Ford Ranger', 'vehicle_type': 'Pickup', 'seat_count': 4, 'sort_order': 71},
    {'brand': 'Ford', 'model_name': 'F-150', 'display_name': 'Ford F-150', 'vehicle_type': 'Pickup', 'seat_count': 4, 'sort_order': 72},
    {'brand': 'Mazda', 'model_name': 'Mazda 3', 'display_name': 'Mazda 3', 'vehicle_type': 'Sedan', 'seat_count': 4, 'sort_order': 73},
    {'brand': 'Mazda', 'model_name': 'CX-5', 'display_name': 'Mazda CX-5', 'vehicle_type': 'SUV', 'seat_count': 4, 'sort_order': 74},
    {'brand': 'Mazda', 'model_name': 'CX-8', 'display_name': 'Mazda CX-8', 'vehicle_type': 'SUV', 'seat_count': 7, 'sort_order': 75},
    {'brand': 'Mazda', 'model_name': 'CX-30', 'display_name': 'Mazda CX-30', 'vehicle_type': 'Crossover', 'seat_count': 4, 'sort_order': 76},
    {'brand': 'Mazda', 'model_name': 'BT-50', 'display_name': 'Mazda BT-50', 'vehicle_type': 'Pickup', 'seat_count': 4, 'sort_order': 77},
    {'brand': 'Nissan', 'model_name': 'Almera', 'display_name': 'Nissan Almera', 'vehicle_type': 'Sedan', 'seat_count': 4, 'sort_order': 78},
    {'brand': 'Nissan', 'model_name': 'Kicks e-POWER', 'display_name': 'Nissan Kicks e-POWER', 'vehicle_type': 'Compact SUV', 'seat_count': 4, 'sort_order': 79},
    {'brand': 'Nissan', 'model_name': 'Serena', 'display_name': 'Nissan Serena', 'vehicle_type': 'MPV', 'seat_count': 7, 'sort_order': 80},
    {'brand': 'Nissan', 'model_name': 'Patrol', 'display_name': 'Nissan Patrol', 'vehicle_type': 'SUV', 'seat_count': 7, 'sort_order': 81},
    {'brand': 'Mitsubishi', 'model_name': 'Xpander Cross', 'display_name': 'Mitsubishi Xpander Cross', 'vehicle_type': 'Crossover MPV', 'seat_count': 7, 'sort_order': 82},
    {'brand': 'Mitsubishi', 'model_name': 'Outlander', 'display_name': 'Mitsubishi Outlander', 'vehicle_type': 'SUV', 'seat_count': 7, 'sort_order': 83},
    {'brand': 'Mitsubishi', 'model_name': 'Attrage', 'display_name': 'Mitsubishi Attrage', 'vehicle_type': 'Sedan', 'seat_count': 4, 'sort_order': 84},
    {'brand': 'Honda', 'model_name': 'Accord', 'display_name': 'Honda Accord', 'vehicle_type': 'Sedan', 'seat_count': 4, 'sort_order': 85},
    {'brand': 'Honda', 'model_name': 'BR-V', 'display_name': 'Honda BR-V', 'vehicle_type': 'MPV', 'seat_count': 7, 'sort_order': 86},
    {'brand': 'Honda', 'model_name': 'Odyssey', 'display_name': 'Honda Odyssey', 'vehicle_type': 'MPV', 'seat_count': 7, 'sort_order': 87},
    {'brand': 'Mercedes-Benz', 'model_name': 'E-Class', 'display_name': 'Mercedes-Benz E-Class', 'vehicle_type': 'Luxury Sedan', 'seat_count': 4, 'sort_order': 88},
    {'brand': 'Mercedes-Benz', 'model_name': 'S-Class', 'display_name': 'Mercedes-Benz S-Class', 'vehicle_type': 'Luxury Sedan', 'seat_count': 4, 'sort_order': 89},
    {'brand': 'Mercedes-Benz', 'model_name': 'GLC', 'display_name': 'Mercedes-Benz GLC', 'vehicle_type': 'Luxury SUV', 'seat_count': 4, 'sort_order': 90},
    {'brand': 'Mercedes-Benz', 'model_name': 'GLE', 'display_name': 'Mercedes-Benz GLE', 'vehicle_type': 'Luxury SUV', 'seat_count': 7, 'sort_order': 91},
    {'brand': 'Mercedes-Benz', 'model_name': 'V-Class', 'display_name': 'Mercedes-Benz V-Class', 'vehicle_type': 'VIP Van', 'seat_count': 7, 'sort_order': 92},
    {'brand': 'Mercedes-Benz', 'model_name': 'Sprinter', 'display_name': 'Mercedes-Benz Sprinter', 'vehicle_type': 'Minibus', 'seat_count': 16, 'sort_order': 93},
    {'brand': 'Mercedes-Benz', 'model_name': 'G-Class', 'display_name': 'Mercedes-Benz G-Class', 'vehicle_type': 'Luxury SUV', 'seat_count': 4, 'sort_order': 94},
    {'brand': 'BMW', 'model_name': '5 Series', 'display_name': 'BMW 5 Series', 'vehicle_type': 'Luxury Sedan', 'seat_count': 4, 'sort_order': 95},
    {'brand': 'BMW', 'model_name': '7 Series', 'display_name': 'BMW 7 Series', 'vehicle_type': 'Luxury Sedan', 'seat_count': 4, 'sort_order': 96},
    {'brand': 'BMW', 'model_name': 'X5', 'display_name': 'BMW X5', 'vehicle_type': 'Luxury SUV', 'seat_count': 7, 'sort_order': 97},
    {'brand': 'BMW', 'model_name': 'X7', 'display_name': 'BMW X7', 'vehicle_type': 'Luxury SUV', 'seat_count': 7, 'sort_order': 98},
    {'brand': 'BYD', 'model_name': 'Seal', 'display_name': 'BYD Seal', 'vehicle_type': 'Electric Sedan', 'seat_count': 4, 'sort_order': 99},
    {'brand': 'BYD', 'model_name': 'Han', 'display_name': 'BYD Han', 'vehicle_type': 'Electric Sedan', 'seat_count': 4, 'sort_order': 100},
    {'brand': 'Tank', 'model_name': 'Tank 300', 'display_name': 'Tank 300', 'vehicle_type': 'Off-road SUV', 'seat_count': 4, 'sort_order': 101},
    {'brand': 'Geely', 'model_name': 'Coolray', 'display_name': 'Geely Coolray', 'vehicle_type': 'Crossover', 'seat_count': 4, 'sort_order': 102},
    {'brand': 'Geely', 'model_name': 'Monjaro', 'display_name': 'Geely Monjaro', 'vehicle_type': 'SUV', 'seat_count': 4, 'sort_order': 103},
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
