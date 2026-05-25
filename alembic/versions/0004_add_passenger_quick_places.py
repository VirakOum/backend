"""Add passenger quick places

Revision ID: 0004_passenger_quick_places
Revises: 0003_auth_tokens
Create Date: 2026-05-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0004_passenger_quick_places"
down_revision = "0003_auth_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "passenger_quick_places",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key", sa.String(length=20), nullable=False),
        sa.Column("label", sa.String(length=50), nullable=False),
        sa.Column("address_line", sa.String(length=255), nullable=False),
        sa.Column("lat", sa.Numeric(10, 6), nullable=False),
        sa.Column("lng", sa.Numeric(10, 6), nullable=False),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "key", name="uq_passenger_quick_places_user_key"),
    )


def downgrade() -> None:
    op.drop_table("passenger_quick_places")
