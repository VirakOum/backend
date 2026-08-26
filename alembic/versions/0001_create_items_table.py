"""create items table

Revision ID: 0001_create_items_table
Revises:
Create Date: 2026-05-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0001_create_items_table"
down_revision = None
branch_labels = None
depends_on = None

DEFAULT_ITEMS = [
    {"name": "Phnom Penh - Siem Reap Express Pass", "description": "Standard passenger seat ticket for Phnom Penh to Siem Reap route."},
    {"name": "Phnom Penh - Sihanoukville VIP Van Seat", "description": "VIP luxury seat with complimentary Wi-Fi & water."},
    {"name": "Heavy Cargo Luggage Pass (Up to 30kg)", "description": "Additional luggage allocation for heavy bags or boxes."},
    {"name": "Inter-City Express Parcel Shipping", "description": "Same-day express parcel drop-off and pickup service."},
    {"name": "Driver Pro Monthly Membership Pass", "description": "0% commission fee driver membership subscription pass."},
    {"name": "Pet Friendly Passenger Transport Pass", "description": "Special allowance for small pet travel in designated vehicle."},
    {"name": "Phnom Penh - Battambang Shuttle Ticket", "description": "Daily passenger shuttle service ticket between PP and Battambang."},
]


def upgrade() -> None:
    items_table = op.create_table(
        "items",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=300), nullable=True),
    )

    op.bulk_insert(items_table, DEFAULT_ITEMS)


def downgrade() -> None:
    op.drop_table("items")
