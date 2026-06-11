from datetime import date, datetime
from uuid import UUID
from typing import Literal

from pydantic import BaseModel, ConfigDict


DriverMembershipCode = Literal["normal", "pro", "vip"]
DriverMembershipStatus = Literal["active", "expired", "cancelled", "scheduled"]
DriverInvoiceType = Literal["service_fee", "subscription"]
DriverInvoiceStatus = Literal["pending", "issued", "paid", "overdue", "failed", "void"]


class DriverMembershipSummary(BaseModel):
    code: DriverMembershipCode
    label: str
    monthly_subscription_usd: float
    monthly_subscription_khr: int
    service_fee_per_passenger_usd: float
    service_fee_per_passenger_khr: int
    verified_badge: bool = False
    priority_bookings: bool = False
    started_at: datetime | None = None
    next_billing_at: datetime | None = None
    status: DriverMembershipStatus = "active"


class DriverWalletSummary(BaseModel):
    service_fee_owed_usd: float = 0.0
    service_fee_owed_khr: int = 0
    subscription_fee_owed_usd: float = 0.0
    subscription_fee_owed_khr: int = 0
    total_owed_usd: float = 0.0
    total_owed_khr: int = 0
    last_settled_at: datetime | None = None


class DriverFeeAggregate(BaseModel):
    completed_bookings: int = 0
    confirmed_passengers: int = 0
    service_fee_usd: float = 0.0
    service_fee_khr: int = 0


class DriverDailyFeeSummaryRead(BaseModel):
    date: date
    completed_bookings: int = 0
    confirmed_passengers: int = 0
    service_fee_usd: float = 0.0
    service_fee_khr: int = 0
    membership_label: str
    invoice_status: DriverInvoiceStatus = "pending"


class DriverInvoiceSummaryRead(BaseModel):
    id: UUID
    type: DriverInvoiceType
    status: DriverInvoiceStatus
    period_label: str
    total_usd: float
    total_khr: int
    issued_at: datetime | None = None
    due_at: datetime | None = None
    paid_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class DriverFeeSummaryResponse(BaseModel):
    driver_id: UUID
    as_of: datetime
    timezone: str = "Asia/Phnom_Penh"
    membership: DriverMembershipSummary
    wallet: DriverWalletSummary
    today: DriverFeeAggregate
    period: DriverFeeAggregate
    daily_summaries: list[DriverDailyFeeSummaryRead]
    invoices: list[DriverInvoiceSummaryRead]
