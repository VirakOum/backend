from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db import get_db
from ..models import Booking, Trip, User, phnom_penh_now
from ..models_driver_fee import (
    DriverDailyFeeSummary,
    DriverInvoice,
    DriverMembership,
    DriverWallet,
)
from ..schemas_driver_fee import (
    DriverDailyFeeSummaryRead,
    DriverFeeAggregate,
    DriverFeeSummaryResponse,
    DriverInvoiceSummaryRead,
    DriverMembershipSummary,
    DriverWalletSummary,
)

router = APIRouter(prefix="/travel/wallet", tags=["driver-wallet"])

DEFAULT_TIMEZONE = "Asia/Phnom_Penh"
USD_TO_KHR = 4000
BILLABLE_BOOKING_STATUSES = {"confirmed"}
UNPAID_INVOICE_STATUSES = {"pending", "issued", "overdue", "failed"}

MEMBERSHIP_CATALOG = {
    "normal": {
        "code": "normal",
        "label": "Normal User",
        "monthly_subscription_usd": Decimal("0.00"),
        "monthly_subscription_khr": 0,
        "service_fee_per_passenger_usd": Decimal("1.00"),
        "service_fee_per_passenger_khr": 4000,
        "verified_badge": False,
        "priority_bookings": False,
        "status": "active",
    },
    "pro": {
        "code": "pro",
        "label": "Membership Pro",
        "monthly_subscription_usd": Decimal("50.00"),
        "monthly_subscription_khr": 200000,
        "service_fee_per_passenger_usd": Decimal("0.50"),
        "service_fee_per_passenger_khr": 2000,
        "verified_badge": True,
        "priority_bookings": True,
        "status": "active",
    },
    "vip": {
        "code": "vip",
        "label": "VIP",
        "monthly_subscription_usd": Decimal("150.00"),
        "monthly_subscription_khr": 600000,
        "service_fee_per_passenger_usd": Decimal("0.25"),
        "service_fee_per_passenger_khr": 1000,
        "verified_badge": True,
        "priority_bookings": True,
        "status": "active",
    },
}


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _to_float(value: Decimal | float | int | None) -> float:
    if value is None:
        return 0.0
    return float(value)


def _to_int(value: int | Decimal | None) -> int:
    if value is None:
        return 0
    if isinstance(value, Decimal):
        return int(value)
    return int(value)


def _default_membership_summary() -> DriverMembershipSummary:
    data = MEMBERSHIP_CATALOG["normal"]
    return DriverMembershipSummary(
        code=data["code"],
        label=data["label"],
        monthly_subscription_usd=float(data["monthly_subscription_usd"]),
        monthly_subscription_khr=data["monthly_subscription_khr"],
        service_fee_per_passenger_usd=float(data["service_fee_per_passenger_usd"]),
        service_fee_per_passenger_khr=data["service_fee_per_passenger_khr"],
        verified_badge=data["verified_badge"],
        priority_bookings=data["priority_bookings"],
        status=data["status"],
    )


def _build_membership_summary(membership: DriverMembership | None) -> DriverMembershipSummary:
    if membership is None:
        return _default_membership_summary()
    return DriverMembershipSummary(
        code=membership.code,
        label=membership.label,
        monthly_subscription_usd=_to_float(membership.monthly_subscription_usd),
        monthly_subscription_khr=_to_int(membership.monthly_subscription_khr),
        service_fee_per_passenger_usd=_to_float(membership.service_fee_per_passenger_usd),
        service_fee_per_passenger_khr=_to_int(membership.service_fee_per_passenger_khr),
        verified_badge=membership.verified_badge,
        priority_bookings=membership.priority_bookings,
        started_at=membership.started_at,
        next_billing_at=membership.next_billing_at,
        status=membership.status,
    )


def _empty_aggregate() -> DriverFeeAggregate:
    return DriverFeeAggregate(
        completed_bookings=0,
        confirmed_passengers=0,
        service_fee_usd=0.0,
        service_fee_khr=0,
    )


def _aggregate_from_summaries(
    summaries: list[DriverDailyFeeSummaryRead],
    *,
    start_date: date,
    end_date: date,
) -> DriverFeeAggregate:
    completed_bookings = 0
    confirmed_passengers = 0
    service_fee_usd = Decimal("0.00")
    service_fee_khr = 0

    for summary in summaries:
        if start_date <= summary.date <= end_date:
            completed_bookings += summary.completed_bookings
            confirmed_passengers += summary.confirmed_passengers
            service_fee_usd += Decimal(str(summary.service_fee_usd))
            service_fee_khr += summary.service_fee_khr

    return DriverFeeAggregate(
        completed_bookings=completed_bookings,
        confirmed_passengers=confirmed_passengers,
        service_fee_usd=float(_money(service_fee_usd)),
        service_fee_khr=service_fee_khr,
    )


def _fallback_daily_summaries(
    bookings: list[Booking],
    membership: DriverMembershipSummary,
) -> list[DriverDailyFeeSummaryRead]:
    grouped: dict[date, dict[str, int | Decimal]] = defaultdict(
        lambda: {
            "completed_bookings": 0,
            "confirmed_passengers": 0,
            "service_fee_usd": Decimal("0.00"),
            "service_fee_khr": 0,
        }
    )

    for booking in bookings:
        summary_date = booking.created_at.date()
        passengers = len(booking.seat_numbers or [])
        bucket = grouped[summary_date]
        bucket["completed_bookings"] += 1
        bucket["confirmed_passengers"] += passengers
        bucket["service_fee_usd"] += (
            Decimal(str(membership.service_fee_per_passenger_usd)) * Decimal(passengers)
        )
        bucket["service_fee_khr"] += membership.service_fee_per_passenger_khr * passengers

    summaries: list[DriverDailyFeeSummaryRead] = []
    for summary_date, values in grouped.items():
        summaries.append(
            DriverDailyFeeSummaryRead(
                date=summary_date,
                completed_bookings=int(values["completed_bookings"]),
                confirmed_passengers=int(values["confirmed_passengers"]),
                service_fee_usd=float(_money(values["service_fee_usd"])),
                service_fee_khr=int(values["service_fee_khr"]),
                membership_label=membership.label,
                invoice_status="pending",
            )
        )

    summaries.sort(key=lambda item: item.date, reverse=True)
    return summaries


def _load_daily_summaries(
    db: Session,
    *,
    driver_id,
    membership: DriverMembershipSummary,
) -> list[DriverDailyFeeSummaryRead]:
    rows = db.execute(
        select(DriverDailyFeeSummary)
        .where(DriverDailyFeeSummary.driver_id == driver_id)
        .order_by(DriverDailyFeeSummary.summary_date.desc())
    ).scalars().all()

    if rows:
        return [
            DriverDailyFeeSummaryRead(
                date=row.summary_date,
                completed_bookings=row.completed_bookings,
                confirmed_passengers=row.confirmed_passengers,
                service_fee_usd=_to_float(row.service_fee_usd),
                service_fee_khr=_to_int(row.service_fee_khr),
                membership_label=row.membership_label,
                invoice_status=row.invoice_status,
            )
            for row in rows
        ]

    bookings = db.execute(
        select(Booking)
        .join(Trip, Booking.trip_id == Trip.id)
        .where(
            Trip.driver_id == driver_id,
            Booking.status.in_(BILLABLE_BOOKING_STATUSES),
        )
        .order_by(Booking.created_at.desc())
    ).scalars().all()
    return _fallback_daily_summaries(bookings, membership)


def _load_invoices(db: Session, *, driver_id) -> list[DriverInvoiceSummaryRead]:
    rows = db.execute(
        select(DriverInvoice)
        .where(DriverInvoice.driver_id == driver_id)
        .order_by(DriverInvoice.created_at.desc())
        .limit(20)
    ).scalars().all()

    return [
        DriverInvoiceSummaryRead(
            id=row.id,
            type=row.type,
            status=row.status,
            period_label=row.period_label,
            total_usd=_to_float(row.total_usd),
            total_khr=_to_int(row.total_khr),
            issued_at=row.issued_at,
            due_at=row.due_at,
            paid_at=row.paid_at,
        )
        for row in rows
    ]


def _derive_wallet(
    *,
    wallet: DriverWallet | None,
    invoices: list[DriverInvoiceSummaryRead],
    daily_summaries: list[DriverDailyFeeSummaryRead],
) -> DriverWalletSummary:
    if wallet is not None:
        return DriverWalletSummary(
            service_fee_owed_usd=_to_float(wallet.service_fee_owed_usd),
            service_fee_owed_khr=_to_int(wallet.service_fee_owed_khr),
            subscription_fee_owed_usd=_to_float(wallet.subscription_fee_owed_usd),
            subscription_fee_owed_khr=_to_int(wallet.subscription_fee_owed_khr),
            total_owed_usd=_to_float(wallet.total_owed_usd),
            total_owed_khr=_to_int(wallet.total_owed_khr),
            last_settled_at=wallet.last_settled_at,
        )

    unpaid_invoices = [invoice for invoice in invoices if invoice.status in UNPAID_INVOICE_STATUSES]
    service_fee_owed_usd = Decimal("0.00")
    service_fee_owed_khr = 0
    subscription_fee_owed_usd = Decimal("0.00")
    subscription_fee_owed_khr = 0

    if unpaid_invoices:
        for invoice in unpaid_invoices:
            if invoice.type == "service_fee":
                service_fee_owed_usd += Decimal(str(invoice.total_usd))
                service_fee_owed_khr += invoice.total_khr
            elif invoice.type == "subscription":
                subscription_fee_owed_usd += Decimal(str(invoice.total_usd))
                subscription_fee_owed_khr += invoice.total_khr
    else:
        for summary in daily_summaries:
            service_fee_owed_usd += Decimal(str(summary.service_fee_usd))
            service_fee_owed_khr += summary.service_fee_khr

    total_owed_usd = service_fee_owed_usd + subscription_fee_owed_usd
    total_owed_khr = service_fee_owed_khr + subscription_fee_owed_khr
    settled_at_candidates = [invoice.paid_at for invoice in invoices if invoice.paid_at is not None]

    return DriverWalletSummary(
        service_fee_owed_usd=float(_money(service_fee_owed_usd)),
        service_fee_owed_khr=service_fee_owed_khr,
        subscription_fee_owed_usd=float(_money(subscription_fee_owed_usd)),
        subscription_fee_owed_khr=subscription_fee_owed_khr,
        total_owed_usd=float(_money(total_owed_usd)),
        total_owed_khr=total_owed_khr,
        last_settled_at=max(settled_at_candidates) if settled_at_candidates else None,
    )


@router.get("/driver-fee-summary", response_model=DriverFeeSummaryResponse)
def get_driver_fee_summary(
    days: int = Query(default=30, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DriverFeeSummaryResponse:
    if current_user.role != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can access driver fee summary")

    now = phnom_penh_now()
    today = now.date()
    period_start = today - timedelta(days=days - 1)

    membership_row = db.execute(
        select(DriverMembership)
        .where(DriverMembership.driver_id == current_user.id)
        .order_by(DriverMembership.started_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    membership = _build_membership_summary(membership_row)

    daily_summaries = _load_daily_summaries(
        db,
        driver_id=current_user.id,
        membership=membership,
    )
    invoices = _load_invoices(db, driver_id=current_user.id)
    wallet_row = db.execute(
        select(DriverWallet).where(DriverWallet.driver_id == current_user.id)
    ).scalar_one_or_none()
    wallet = _derive_wallet(
        wallet=wallet_row,
        invoices=invoices,
        daily_summaries=daily_summaries,
    )

    today_summary = _aggregate_from_summaries(
        daily_summaries,
        start_date=today,
        end_date=today,
    )
    period_summary = _aggregate_from_summaries(
        daily_summaries,
        start_date=period_start,
        end_date=today,
    )

    return DriverFeeSummaryResponse(
        driver_id=current_user.id,
        as_of=now,
        timezone=DEFAULT_TIMEZONE,
        membership=membership,
        wallet=wallet,
        today=today_summary,
        period=period_summary,
        daily_summaries=daily_summaries[: min(days, len(daily_summaries))],
        invoices=invoices,
    )
