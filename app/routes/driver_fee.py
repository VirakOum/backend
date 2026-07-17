from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..config import (
    AUTO_LOCK_DRIVER_ON_DEBT_LIMIT,
    DEFAULT_DRIVER_CASH_DEBT_LIMIT_KHR,
    DEFAULT_DRIVER_CASH_DEBT_LIMIT_USD,
    ENABLE_DIGITAL_PAYMENT,
)
from ..db import get_db
from ..models import (
    AppRuntimeSetting,
    Booking,
    DriverDailyFeeSummary,
    DriverInvoice,
    DriverMembership,
    DriverWallet,
    DriverWalletEntry,
    Trip,
    User,
    phnom_penh_now,
)
from ..schemas import (
    DriverDailyFeeSummaryRead,
    DriverFeeAggregate,
    DriverFeeSummaryResponse,
    DriverInvoiceSummaryRead,
    DriverMembershipSummary,
    DriverWalletEntryRead,
    DriverWalletSummary,
)

router = APIRouter(prefix="/travel/wallet", tags=["driver-wallet"])

DEFAULT_TIMEZONE = "Asia/Phnom_Penh"
SETTLEMENT_ENTRY_STATUSES = {"owed", "settled"}
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
    return int(value)


def snapshot_booking_fees(db: Session, booking: Booking) -> None:
    """Snapshot the driver's membership fee onto a booking once it becomes billable."""
    if booking.fee_snapshotted_at is not None:
        return

    trip = db.execute(select(Trip).where(Trip.id == booking.trip_id)).scalar_one_or_none()
    if trip is None:
        return

    membership = db.execute(
        select(DriverMembership)
        .where(DriverMembership.driver_id == trip.driver_id)
        .order_by(DriverMembership.started_at.desc())
        .limit(1)
    ).scalar_one_or_none()

    if membership is None:
        code = "normal"
        label = "Normal User"
        fee_usd = Decimal("1.00")
        fee_khr = 4000
    else:
        code = membership.code
        label = membership.label
        fee_usd = membership.service_fee_per_passenger_usd
        fee_khr = membership.service_fee_per_passenger_khr

    passengers = len(booking.seat_numbers or [])
    total_usd = Decimal(str(fee_usd)) * passengers
    total_khr = int(fee_khr) * passengers

    booking.membership_code_snapshot = code
    booking.membership_label_snapshot = label
    booking.service_fee_per_passenger_usd = float(fee_usd)
    booking.service_fee_per_passenger_khr = int(fee_khr)
    booking.service_fee_total_usd = float(_money(total_usd))
    booking.service_fee_total_khr = total_khr
    booking.fee_snapshotted_at = phnom_penh_now()
    booking.settlement_summary_date = phnom_penh_now().date()


def _get_runtime_settings(db: Session) -> AppRuntimeSetting:
    try:
        settings = db.execute(
            select(AppRuntimeSetting).where(AppRuntimeSetting.id == 1)
        ).scalar_one_or_none()
    except OperationalError:
        return AppRuntimeSetting(
            id=1,
            enable_digital_payment=ENABLE_DIGITAL_PAYMENT,
            auto_lock_on_limit=AUTO_LOCK_DRIVER_ON_DEBT_LIMIT,
            driver_cash_debt_limit_usd=DEFAULT_DRIVER_CASH_DEBT_LIMIT_USD,
            driver_cash_debt_limit_khr=DEFAULT_DRIVER_CASH_DEBT_LIMIT_KHR,
        )

    if settings is not None:
        return settings

    settings = AppRuntimeSetting(
        id=1,
        enable_digital_payment=ENABLE_DIGITAL_PAYMENT,
        auto_lock_on_limit=AUTO_LOCK_DRIVER_ON_DEBT_LIMIT,
        driver_cash_debt_limit_usd=DEFAULT_DRIVER_CASH_DEBT_LIMIT_USD,
        driver_cash_debt_limit_khr=DEFAULT_DRIVER_CASH_DEBT_LIMIT_KHR,
    )
    db.add(settings)
    db.flush()
    return settings


def get_runtime_settings(db: Session) -> AppRuntimeSetting:
    return _get_runtime_settings(db)


def _get_or_create_driver_wallet(db: Session, *, driver_id) -> DriverWallet:
    try:
        wallet = db.execute(
            select(DriverWallet).where(DriverWallet.driver_id == driver_id)
        ).scalar_one_or_none()
    except OperationalError:
        settings = _get_runtime_settings(db)
        return DriverWallet(
            driver_id=driver_id,
            credit_limit_usd=float(settings.driver_cash_debt_limit_usd),
            credit_limit_khr=int(settings.driver_cash_debt_limit_khr),
            is_locked=False,
            total_owed_usd=0,
            total_owed_khr=0,
            service_fee_owed_usd=0,
            service_fee_owed_khr=0,
            subscription_fee_owed_usd=0,
            subscription_fee_owed_khr=0,
        )

    if wallet is not None:
        return wallet

    settings = _get_runtime_settings(db)
    wallet = DriverWallet(
        driver_id=driver_id,
        credit_limit_usd=float(settings.driver_cash_debt_limit_usd),
        credit_limit_khr=int(settings.driver_cash_debt_limit_khr),
        is_locked=False,
    )
    db.add(wallet)
    db.flush()
    return wallet


def get_or_create_driver_wallet(db: Session, *, driver_id) -> DriverWallet:
    return _get_or_create_driver_wallet(db, driver_id=driver_id)


def evaluate_driver_wallet_lock(
    db: Session,
    *,
    wallet: DriverWallet,
    settings: AppRuntimeSetting | None = None,
) -> DriverWallet:
    settings = settings or _get_runtime_settings(db)
    wallet.credit_limit_usd = float(settings.driver_cash_debt_limit_usd)
    wallet.credit_limit_khr = int(settings.driver_cash_debt_limit_khr)

    over_limit = (
        float(wallet.total_owed_usd or 0) >= float(wallet.credit_limit_usd or 0)
        or int(wallet.total_owed_khr or 0) >= int(wallet.credit_limit_khr or 0)
    )
    if getattr(wallet, "admin_locked", False):
        wallet.is_locked = True
        wallet.locked_reason = getattr(wallet, "admin_locked_reason", None) or "Locked by administrator."
    elif settings.auto_lock_on_limit and over_limit:
        wallet.is_locked = True
        wallet.locked_reason = (
            "Driver debt limit reached. Please settle wallet debt before publishing new trips."
        )
    else:
        wallet.is_locked = False
        wallet.locked_reason = None
    return wallet


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
    entries: list[DriverWalletEntry],
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

    for entry in entries:
        summary_date = entry.posted_at.date()
        passengers = int(entry.passenger_count or 0)
        bucket = grouped[summary_date]
        bucket["completed_bookings"] += 1
        bucket["confirmed_passengers"] += passengers
        bucket["service_fee_usd"] += Decimal(str(entry.service_fee_usd or 0))
        bucket["service_fee_khr"] += int(entry.service_fee_khr or 0)

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

    entries = db.execute(
        select(DriverWalletEntry)
        .where(
            DriverWalletEntry.driver_id == driver_id,
            DriverWalletEntry.status.in_(SETTLEMENT_ENTRY_STATUSES),
        )
        .order_by(DriverWalletEntry.posted_at.desc())
    ).scalars().all()
    return _fallback_daily_summaries(entries, membership)


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
            credit_limit_usd=_to_float(wallet.credit_limit_usd),
            credit_limit_khr=_to_int(wallet.credit_limit_khr),
            is_locked=wallet.is_locked,
            locked_reason=wallet.locked_reason,
            last_entry_posted_at=wallet.last_entry_posted_at,
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
        credit_limit_usd=DEFAULT_DRIVER_CASH_DEBT_LIMIT_USD,
        credit_limit_khr=DEFAULT_DRIVER_CASH_DEBT_LIMIT_KHR,
        is_locked=False,
        locked_reason=None,
        last_entry_posted_at=None,
        last_settled_at=max(settled_at_candidates) if settled_at_candidates else None,
    )


def _load_recent_entries(
    db: Session,
    *,
    driver_id,
    limit: int = 12,
) -> list[DriverWalletEntryRead]:
    rows = db.execute(
        select(DriverWalletEntry)
        .where(DriverWalletEntry.driver_id == driver_id)
        .order_by(DriverWalletEntry.posted_at.desc())
        .limit(limit)
    ).scalars().all()

    return [
        DriverWalletEntryRead(
            entry_id=row.id,
            trip_id=row.trip_id,
            booking_id=row.booking_id,
            payment_method=row.payment_method,
            entry_type=row.entry_type,
            membership_tier=row.membership_code_snapshot,
            membership_label=row.membership_label_snapshot,
            passenger_count=row.passenger_count,
            cash_collected_khr=row.cash_collected_khr,
            service_fee_usd=_to_float(row.service_fee_usd),
            service_fee_khr=_to_int(row.service_fee_khr),
            status=row.status,
            posted_at=row.posted_at,
            settled_at=row.settled_at,
        )
        for row in rows
    ]


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
    settings = _get_runtime_settings(db)

    daily_summaries = _load_daily_summaries(
        db,
        driver_id=current_user.id,
        membership=membership,
    )
    invoices = _load_invoices(db, driver_id=current_user.id)
    wallet_row = _get_or_create_driver_wallet(db, driver_id=current_user.id)
    evaluate_driver_wallet_lock(db, wallet=wallet_row, settings=settings)
    wallet = _derive_wallet(
        wallet=wallet_row,
        invoices=invoices,
        daily_summaries=daily_summaries,
    )
    recent_entries = _load_recent_entries(db, driver_id=current_user.id)

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
        digital_payment_enabled=settings.enable_digital_payment,
        recent_entries=recent_entries,
    )
