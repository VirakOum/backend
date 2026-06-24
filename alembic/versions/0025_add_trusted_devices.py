"""Add trusted devices for device-based re-login

Revision ID: 0025_add_trusted_devices
Revises: 0024_separate_trip_live_coordinates
Create Date: 2026-06-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0025_add_trusted_devices"
down_revision = "0024_separate_trip_live_coordinates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trusted_devices",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_id_hash", sa.String(length=128), nullable=False),
        sa.Column("device_secret_hash", sa.String(length=128), nullable=False),
        sa.Column("device_platform", sa.String(length=30), nullable=False),
        sa.Column("device_name", sa.String(length=120), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("device_id_hash"),
    )
    op.create_index("ix_trusted_devices_device_id_hash", "trusted_devices", ["device_id_hash"])


def downgrade() -> None:
    op.drop_index("ix_trusted_devices_device_id_hash", table_name="trusted_devices")
    op.drop_table("trusted_devices")
