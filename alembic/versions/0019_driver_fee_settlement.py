"""Add driver fee settlement tables and booking fee snapshot fields

Revision ID: 0019_driver_fee_settlement
Revises: 0018_trip_route_stop_fields
Create Date: 2026-06-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0019_driver_fee_settlement"
down_revision = "0018_trip_route_stop_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bookings", sa.Column("membership_code_snapshot", sa.String(length=20), nullable=True))
    op.add_column("bookings", sa.Column("membership_label_snapshot", sa.String(length=50), nullable=True))
    op.add_column("bookings", sa.Column("service_fee_per_passenger_usd", sa.Numeric(10, 2), nullable=True))
    op.add_column("bookings", sa.Column("service_fee_per_passenger_khr", sa.Integer(), nullable=True))
    op.add_column("bookings", sa.Column("service_fee_total_usd", sa.Numeric(10, 2), nullable=True))
    op.add_column("bookings", sa.Column("service_fee_total_khr", sa.Integer(), nullable=True))
    op.add_column("bookings", sa.Column("fee_snapshotted_at", sa.DateTime(), nullable=True))
    op.add_column("bookings", sa.Column("settlement_summary_date", sa.Date(), nullable=True))
    op.create_check_constraint(
        "booking_membership_code_snapshot_check",
        "bookings",
        "membership_code_snapshot IS NULL OR membership_code_snapshot IN ('normal', 'pro', 'vip')",
    )
    op.create_index(
        "ix_bookings_settlement_summary_date",
        "bookings",
        ["settlement_summary_date"],
        unique=False,
    )

    op.create_table(
        "driver_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("label", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("verified_badge", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("priority_bookings", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("monthly_subscription_usd", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("monthly_subscription_khr", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("service_fee_per_passenger_usd", sa.Numeric(10, 2), nullable=False),
        sa.Column("service_fee_per_passenger_khr", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("ends_at", sa.DateTime(), nullable=True),
        sa.Column("next_billing_at", sa.DateTime(), nullable=True),
        sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("code IN ('normal', 'pro', 'vip')", name="driver_membership_code_check"),
        sa.CheckConstraint(
            "status IN ('active', 'expired', 'cancelled', 'scheduled')",
            name="driver_membership_status_check",
        ),
        sa.ForeignKeyConstraint(["driver_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_driver_memberships_driver_id", "driver_memberships", ["driver_id"], unique=False)
    op.create_index(
        "idx_driver_memberships_driver_status",
        "driver_memberships",
        ["driver_id", "status", "started_at"],
        unique=False,
    )

    op.create_table(
        "driver_wallets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("service_fee_owed_usd", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("service_fee_owed_khr", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("subscription_fee_owed_usd", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("subscription_fee_owed_khr", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_owed_usd", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("total_owed_khr", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_settled_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["driver_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("driver_id"),
    )

    op.create_table(
        "driver_daily_fee_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("membership_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("summary_date", sa.Date(), nullable=False),
        sa.Column("membership_code", sa.String(length=20), nullable=False),
        sa.Column("membership_label", sa.String(length=50), nullable=False),
        sa.Column("completed_bookings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("confirmed_passengers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("service_fee_usd", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("service_fee_khr", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("invoice_status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "membership_code IN ('normal', 'pro', 'vip')",
            name="driver_daily_fee_membership_code_check",
        ),
        sa.CheckConstraint(
            "invoice_status IN ('pending', 'issued', 'paid', 'overdue', 'failed', 'void')",
            name="driver_daily_fee_invoice_status_check",
        ),
        sa.ForeignKeyConstraint(["driver_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["membership_id"], ["driver_memberships.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("driver_id", "summary_date", name="uq_driver_daily_fee_driver_date"),
    )
    op.create_index(
        "idx_driver_daily_fee_driver_date",
        "driver_daily_fee_summaries",
        ["driver_id", "summary_date"],
        unique=False,
    )

    op.create_table(
        "driver_invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("membership_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("daily_summary_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("period_label", sa.String(length=100), nullable=False),
        sa.Column("total_usd", sa.Numeric(10, 2), nullable=False),
        sa.Column("total_khr", sa.Integer(), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=True),
        sa.Column("due_at", sa.DateTime(), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("type IN ('service_fee', 'subscription')", name="driver_invoice_type_check"),
        sa.CheckConstraint(
            "status IN ('pending', 'issued', 'paid', 'overdue', 'failed', 'void')",
            name="driver_invoice_status_check",
        ),
        sa.ForeignKeyConstraint(["driver_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["membership_id"], ["driver_memberships.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["daily_summary_id"], ["driver_daily_fee_summaries.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_driver_invoices_driver_created",
        "driver_invoices",
        ["driver_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_driver_invoices_driver_created", table_name="driver_invoices")
    op.drop_table("driver_invoices")

    op.drop_index("idx_driver_daily_fee_driver_date", table_name="driver_daily_fee_summaries")
    op.drop_table("driver_daily_fee_summaries")

    op.drop_table("driver_wallets")

    op.drop_index("idx_driver_memberships_driver_status", table_name="driver_memberships")
    op.drop_index("ix_driver_memberships_driver_id", table_name="driver_memberships")
    op.drop_table("driver_memberships")

    op.drop_index("ix_bookings_settlement_summary_date", table_name="bookings")
    op.drop_constraint("booking_membership_code_snapshot_check", "bookings", type_="check")
    op.drop_column("bookings", "settlement_summary_date")
    op.drop_column("bookings", "fee_snapshotted_at")
    op.drop_column("bookings", "service_fee_total_khr")
    op.drop_column("bookings", "service_fee_total_usd")
    op.drop_column("bookings", "service_fee_per_passenger_khr")
    op.drop_column("bookings", "service_fee_per_passenger_usd")
    op.drop_column("bookings", "membership_label_snapshot")
    op.drop_column("bookings", "membership_code_snapshot")
