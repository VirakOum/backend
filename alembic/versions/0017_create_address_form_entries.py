"""Create address form entries table

Revision ID: 0017_address_form_entries
Revises: 0016_addresses_seed
Create Date: 2026-06-04 00:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0017_address_form_entries"
down_revision = "0016_addresses_seed"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "address_form_entries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("country_code", sa.String(length=20), nullable=False),
        sa.Column("country_name_en", sa.String(length=255), nullable=False),
        sa.Column("country_name_km", sa.String(length=255), nullable=True),
        sa.Column("province_code", sa.String(length=20), nullable=False),
        sa.Column("province_name_en", sa.String(length=255), nullable=False),
        sa.Column("province_name_km", sa.String(length=255), nullable=True),
        sa.Column("district_code", sa.String(length=20), nullable=False),
        sa.Column("district_name_en", sa.String(length=255), nullable=False),
        sa.Column("district_name_km", sa.String(length=255), nullable=True),
        sa.Column("commune_code", sa.String(length=20), nullable=False),
        sa.Column("commune_name_en", sa.String(length=255), nullable=False),
        sa.Column("commune_name_km", sa.String(length=255), nullable=True),
        sa.Column("village_code", sa.String(length=20), nullable=False),
        sa.Column("village_name_en", sa.String(length=255), nullable=False),
        sa.Column("village_name_km", sa.String(length=255), nullable=True),
        sa.Column("detail_line", sa.String(length=255), nullable=True),
        sa.Column("formatted_address_en", sa.Text(), nullable=False),
        sa.Column("formatted_address_km", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_address_form_entries_province_code", "address_form_entries", ["province_code"], unique=False)
    op.create_index("ix_address_form_entries_district_code", "address_form_entries", ["district_code"], unique=False)
    op.create_index("ix_address_form_entries_commune_code", "address_form_entries", ["commune_code"], unique=False)
    op.create_index("ix_address_form_entries_village_code", "address_form_entries", ["village_code"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_address_form_entries_village_code", table_name="address_form_entries")
    op.drop_index("ix_address_form_entries_commune_code", table_name="address_form_entries")
    op.drop_index("ix_address_form_entries_district_code", table_name="address_form_entries")
    op.drop_index("ix_address_form_entries_province_code", table_name="address_form_entries")
    op.drop_table("address_form_entries")
