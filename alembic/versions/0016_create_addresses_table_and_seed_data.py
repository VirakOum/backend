"""Create addresses table and seed Cambodia address hierarchy

Revision ID: 0016_addresses_seed
Revises: 0015_trip_repeat_return
Create Date: 2026-06-04 00:00:00.000000

"""
from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from alembic import op
import sqlalchemy as sa


revision = "0016_addresses_seed"
down_revision = "0015_trip_repeat_return"
branch_labels = None
depends_on = None


def _load_address_rows() -> list[dict]:
    file_path = Path(__file__).resolve().parents[2] / "addresses.json"
    text = file_path.read_text(encoding="utf-8")
    start = text.find("[")
    if start == -1:
        raise ValueError("addresses.json does not contain a JSON array")
    rows, _ = json.JSONDecoder().raw_decode(text[start:])
    if not isinstance(rows, list):
        raise ValueError("addresses.json must decode to a list")
    return rows


def _to_decimal(value: str | None) -> Decimal | None:
    if value in (None, "", "0"):
        return None
    return Decimal(value)


def _normalize_row(row: dict) -> dict:
    return {
        "id": int(row["id"]),
        "code": row["code"],
        "name": row["name"],
        "description": row.get("description"),
        "type": row["type"],
        "parent_code": row.get("parent_code") or None,
        "reference": row.get("reference"),
        "official_note": row.get("official_note"),
        "note_by_checker": row.get("note by_checker"),
        "latitude": _to_decimal(row.get("latitude")),
        "longitude": _to_decimal(row.get("longitude")),
        "lat_lng": row.get("l_l"),
        "o_b": row.get("o_b"),
    }


def upgrade() -> None:
    op.create_table(
        "addresses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("parent_code", sa.String(length=20), nullable=True),
        sa.Column("reference", sa.Text(), nullable=True),
        sa.Column("official_note", sa.Text(), nullable=True),
        sa.Column("note_by_checker", sa.Text(), nullable=True),
        sa.Column("latitude", sa.Numeric(10, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 6), nullable=True),
        sa.Column("lat_lng", sa.String(length=64), nullable=True),
        sa.Column("o_b", sa.String(length=10), nullable=True),
        sa.CheckConstraint(
            "type IN ('country', 'province', 'district', 'commune', 'village', 'city', 'khan', 'sangkat', 'ក្រុង')",
            name="address_type_check",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_addresses_code", "addresses", ["code"], unique=True)
    op.create_index("ix_addresses_type", "addresses", ["type"], unique=False)
    op.create_index("ix_addresses_parent_code", "addresses", ["parent_code"], unique=False)
    op.create_index("idx_addresses_type_parent_code", "addresses", ["type", "parent_code"], unique=False)

    addresses_table = sa.table(
        "addresses",
        sa.column("id", sa.Integer()),
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
        sa.column("description", sa.String()),
        sa.column("type", sa.String()),
        sa.column("parent_code", sa.String()),
        sa.column("reference", sa.Text()),
        sa.column("official_note", sa.Text()),
        sa.column("note_by_checker", sa.Text()),
        sa.column("latitude", sa.Numeric(10, 6)),
        sa.column("longitude", sa.Numeric(10, 6)),
        sa.column("lat_lng", sa.String()),
        sa.column("o_b", sa.String()),
    )

    rows = [_normalize_row(row) for row in _load_address_rows()]
    batch_size = 1000
    for start in range(0, len(rows), batch_size):
        op.bulk_insert(addresses_table, rows[start:start + batch_size])


def downgrade() -> None:
    op.drop_index("idx_addresses_type_parent_code", table_name="addresses")
    op.drop_index("ix_addresses_parent_code", table_name="addresses")
    op.drop_index("ix_addresses_type", table_name="addresses")
    op.drop_index("ix_addresses_code", table_name="addresses")
    op.drop_table("addresses")
