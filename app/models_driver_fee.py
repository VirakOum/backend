from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, date

from .db import Base
from .models import phnom_penh_now


class DriverMembership(Base):
    __tablename__ = "driver_memberships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    label: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    verified_badge: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    priority_bookings: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    monthly_subscription_usd: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    monthly_subscription_khr: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    service_fee_per_passenger_usd: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    service_fee_per_passenger_khr: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now, nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_billing_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now, onupdate=phnom_penh_now, nullable=False)

    __table_args__ = (
        CheckConstraint("code IN ('normal', 'pro', 'vip')", name="driver_membership_code_check"),
        CheckConstraint("status IN ('active', 'expired', 'cancelled', 'scheduled')", name="driver_membership_status_check"),
        Index("idx_driver_memberships_driver_status", "driver_id", "status", "started_at"),
    )


class DriverWallet(Base):
    __tablename__ = "driver_wallets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    service_fee_owed_usd: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    service_fee_owed_khr: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    subscription_fee_owed_usd: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    subscription_fee_owed_khr: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_owed_usd: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    total_owed_khr: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_settled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now, onupdate=phnom_penh_now, nullable=False)


class DriverDailyFeeSummary(Base):
    __tablename__ = "driver_daily_fee_summaries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    membership_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("driver_memberships.id", ondelete="SET NULL"), nullable=True)
    summary_date: Mapped[date] = mapped_column(Date, nullable=False)
    membership_code: Mapped[str] = mapped_column(String(20), nullable=False)
    membership_label: Mapped[str] = mapped_column(String(50), nullable=False)
    completed_bookings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    confirmed_passengers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    service_fee_usd: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    service_fee_khr: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    invoice_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now, onupdate=phnom_penh_now, nullable=False)

    membership: Mapped["DriverMembership | None"] = relationship("DriverMembership")

    __table_args__ = (
        CheckConstraint("membership_code IN ('normal', 'pro', 'vip')", name="driver_daily_fee_membership_code_check"),
        CheckConstraint("invoice_status IN ('pending', 'issued', 'paid', 'overdue', 'failed', 'void')", name="driver_daily_fee_invoice_status_check"),
        UniqueConstraint("driver_id", "summary_date", name="uq_driver_daily_fee_driver_date"),
        Index("idx_driver_daily_fee_driver_date", "driver_id", "summary_date"),
    )


class DriverInvoice(Base):
    __tablename__ = "driver_invoices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    membership_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("driver_memberships.id", ondelete="SET NULL"), nullable=True)
    daily_summary_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("driver_daily_fee_summaries.id", ondelete="SET NULL"), nullable=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_label: Mapped[str] = mapped_column(String(100), nullable=False)
    total_usd: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    total_khr: Mapped[int] = mapped_column(Integer, nullable=False)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now, onupdate=phnom_penh_now, nullable=False)

    membership: Mapped["DriverMembership | None"] = relationship("DriverMembership")
    daily_summary: Mapped["DriverDailyFeeSummary | None"] = relationship("DriverDailyFeeSummary")

    __table_args__ = (
        CheckConstraint("type IN ('service_fee', 'subscription')", name="driver_invoice_type_check"),
        CheckConstraint("status IN ('pending', 'issued', 'paid', 'overdue', 'failed', 'void')", name="driver_invoice_status_check"),
        Index("idx_driver_invoices_driver_created", "driver_id", "created_at"),
    )
