"""Add cash driver debt flow tables and wallet lock fields

Revision ID: 0020_cash_driver_debt_flow
Revises: 0019_driver_fee_settlement
Create Date: 2026-06-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0020_cash_driver_debt_flow"
down_revision = "0019_driver_fee_settlement"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("driver_wallets", sa.Column("credit_limit_usd", sa.Numeric(10, 2), nullable=False, server_default="20"))
    op.add_column("driver_wallets", sa.Column("credit_limit_khr", sa.Integer(), nullable=False, server_default="80000"))
    op.add_column("driver_wallets", sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("driver_wallets", sa.Column("locked_reason", sa.String(length=255), nullable=True))
    op.add_column("driver_wallets", sa.Column("last_entry_posted_at", sa.DateTime(), nullable=True))

    op.drop_constraint("booking_payment_method_check", "bookings", type_="check")
    op.drop_constraint("booking_payment_status_check", "bookings", type_="check")
    op.create_check_constraint(
        "booking_payment_method_check",
        "bookings",
        "payment_method IN ('cash', 'aba', 'wing', 'khqr', 'cash_on_arrival')",
    )
    op.create_check_constraint(
        "booking_payment_status_check",
        "bookings",
        "payment_status IN ('pending', 'paid', 'postpaid', 'opened', 'failed', 'cancelled')",
    )

    op.execute(
        """
        UPDATE bookings
        SET payment_method = 'cash'
        WHERE payment_method = 'cash_on_arrival'
        """
    )

    op.create_table(
        "driver_wallet_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entry_type", sa.String(length=30), nullable=False, server_default="trip_service_fee"),
        sa.Column("payment_method", sa.String(length=20), nullable=False, server_default="cash"),
        sa.Column("membership_code_snapshot", sa.String(length=20), nullable=False),
        sa.Column("membership_label_snapshot", sa.String(length=50), nullable=False),
        sa.Column("passenger_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("cash_collected_khr", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("service_fee_usd", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("service_fee_khr", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="owed"),
        sa.Column("posted_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("settled_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("entry_type IN ('trip_service_fee')", name="driver_wallet_entry_type_check"),
        sa.CheckConstraint(
            "payment_method IN ('cash', 'aba', 'wing', 'khqr', 'cash_on_arrival')",
            name="driver_wallet_entry_payment_method_check",
        ),
        sa.CheckConstraint(
            "membership_code_snapshot IN ('normal', 'pro', 'vip')",
            name="driver_wallet_entry_membership_code_check",
        ),
        sa.CheckConstraint("status IN ('owed', 'settled', 'void')", name="driver_wallet_entry_status_check"),
        sa.ForeignKeyConstraint(["driver_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("booking_id"),
    )
    op.create_index("ix_driver_wallet_entries_driver_id", "driver_wallet_entries", ["driver_id"], unique=False)
    op.create_index("ix_driver_wallet_entries_trip_id", "driver_wallet_entries", ["trip_id"], unique=False)
    op.create_index("ix_driver_wallet_entries_booking_id", "driver_wallet_entries", ["booking_id"], unique=False)
    op.create_index("idx_driver_wallet_entries_driver_posted", "driver_wallet_entries", ["driver_id", "posted_at"], unique=False)

    op.create_table(
        "app_runtime_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enable_digital_payment", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("auto_lock_on_limit", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("driver_cash_debt_limit_usd", sa.Numeric(10, 2), nullable=False, server_default="20"),
        sa.Column("driver_cash_debt_limit_khr", sa.Integer(), nullable=False, server_default="80000"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        """
        INSERT INTO app_runtime_settings (
            id,
            enable_digital_payment,
            auto_lock_on_limit,
            driver_cash_debt_limit_usd,
            driver_cash_debt_limit_khr
        ) VALUES (1, false, true, 20, 80000)
        """
    )


def downgrade() -> None:
    op.drop_table("app_runtime_settings")

    op.drop_index("idx_driver_wallet_entries_driver_posted", table_name="driver_wallet_entries")
    op.drop_index("ix_driver_wallet_entries_booking_id", table_name="driver_wallet_entries")
    op.drop_index("ix_driver_wallet_entries_trip_id", table_name="driver_wallet_entries")
    op.drop_index("ix_driver_wallet_entries_driver_id", table_name="driver_wallet_entries")
    op.drop_table("driver_wallet_entries")

    op.drop_constraint("booking_payment_status_check", "bookings", type_="check")
    op.drop_constraint("booking_payment_method_check", "bookings", type_="check")
    op.create_check_constraint(
        "booking_payment_method_check",
        "bookings",
        "payment_method IN ('khqr', 'cash_on_arrival')",
    )
    op.create_check_constraint(
        "booking_payment_status_check",
        "bookings",
        "payment_status IN ('pending', 'opened', 'paid', 'failed', 'cancelled')",
    )

    op.drop_column("driver_wallets", "last_entry_posted_at")
    op.drop_column("driver_wallets", "locked_reason")
    op.drop_column("driver_wallets", "is_locked")
    op.drop_column("driver_wallets", "credit_limit_khr")
    op.drop_column("driver_wallets", "credit_limit_usd")
