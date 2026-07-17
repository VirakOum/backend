from __future__ import annotations

from datetime import date, datetime, timedelta, time
from decimal import Decimal
from pathlib import Path
from random import Random
import sys
from zoneinfo import ZoneInfo

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.auth import hash_password
from app.db import SessionLocal
from app.models import (
    AppRuntimeSetting,
    Booking,
    DriverDailyFeeSummary,
    DriverInvoice,
    DriverMembership,
    DriverWallet,
    DriverWalletEntry,
    PassengerQuickPlace,
    Payment,
    Trip,
    User,
    Vehicle,
    SystemDiscountTicket,
    SystemAd,
)

PROVINCES = [
    "ភ្នំពេញ",
    "បន្ទាយមានជ័យ",
    "បាត់ដំបង",
    "កំពង់ចាម",
    "កំពង់ឆ្នាំង",
    "កំពង់ស្ពឺ",
    "កំពង់ធំ",
    "កំពត",
    "កណ្ដាល",
    "កោះកុង",
    "ក្រចេះ",
    "មណ្ឌលគិរី",
    "ឧត្តរមានជ័យ",
    "ប៉ៃលិន",
    "ព្រះសីហនុ",
    "ព្រះវិហារ",
    "ពោធិ៍សាត់",
    "ព្រៃវែង",
    "រតនគិរី",
    "សៀមរាប",
    "ស្ទឹងត្រែង",
    "ស្វាយរៀង",
    "តាកែវ",
    "ត្បូងឃ្មុំ",
    "កែប",
]

SEAT_TYPE_SPECS = {
    4: {"model": "Toyota Prius", "vehicle_type": "Car", "color": "White", "price": Decimal("25000.00"), "booked_count": 1},
    15: {"model": "Toyota Hiace", "vehicle_type": "Van", "color": "Silver", "price": Decimal("32000.00"), "booked_count": 3},
    16: {"model": "Hyundai H-1", "vehicle_type": "Van", "color": "Black", "price": Decimal("36000.00"), "booked_count": 4},
    23: {"model": "Hyundai Universe Sleeper", "vehicle_type": "Sleeping Bus", "color": "Gold", "price": Decimal("45000.00"), "booked_count": 5},
    30: {"model": "Toyota Coaster", "vehicle_type": "Mini Bus", "color": "Blue", "price": Decimal("30000.00"), "booked_count": 6},
    45: {"model": "Hyundai Universe", "vehicle_type": "Bus", "color": "Red", "price": Decimal("27000.00"), "booked_count": 8},
}


def get_or_create_user(
    db,
    *,
    phone: str,
    full_name: str,
    role: str,
    password: str,
    avatar_url: str | None = None,
    is_verified: bool = True,
    rating_avg: Decimal = Decimal("0.00"),
    rating_count: int = 0,
    completed_trips: int = 0,
) -> User:
    user = db.execute(select(User).where(User.phone == phone)).scalar_one_or_none()
    password_hash = hash_password(password)
    if user is None:
        user = User(
            phone=phone,
            full_name=full_name,
            role=role,
            password_hash=password_hash,
            avatar_url=avatar_url,
            is_verified=is_verified,
            rating_avg=rating_avg,
            rating_count=rating_count,
            completed_trips=completed_trips,
        )
        db.add(user)
        db.flush()
        return user
    user.full_name = full_name
    user.role = role
    user.password_hash = password_hash
    user.avatar_url = avatar_url
    user.is_verified = is_verified
    user.rating_avg = rating_avg
    user.rating_count = rating_count
    user.completed_trips = completed_trips
    db.flush()
    return user


def get_or_create_vehicle(
    db,
    *,
    owner: User,
    plate_number: str,
    seat_type: int,
    model: str,
    company_name: str,
    vehicle_type: str | None = None,
    color: str | None = None,
) -> Vehicle:
    vehicle = db.execute(select(Vehicle).where(Vehicle.plate_number == plate_number)).scalar_one_or_none()
    if vehicle is None:
        vehicle = Vehicle(owner_id=owner.id, plate_number=plate_number, seat_type=seat_type, model=model, company_name=company_name, vehicle_type=vehicle_type, color=color)
        db.add(vehicle)
        db.flush()
        return vehicle
    vehicle.owner_id = owner.id
    vehicle.seat_type = seat_type
    vehicle.model = model
    vehicle.company_name = company_name
    vehicle.vehicle_type = vehicle_type
    vehicle.color = color
    db.flush()
    return vehicle


def get_or_create_trip(
    db,
    *,
    driver: User,
    vehicle: Vehicle,
    departure_province: str,
    destination_province: str,
    departure_time: datetime,
    departure_lat: Decimal | None,
    departure_lng: Decimal | None,
    live_heading: int | None,
    live_speed_kph: Decimal | None,
    live_location_updated_at: datetime | None,
    live_location_expires_at: datetime | None,
    auto_repeat_weekly: bool,
    recurring_day_of_week: int | None,
    recurring_departure_time: time | None,
    price_per_seat: Decimal,
    total_seats: int,
    available_seats: int,
    status: str = "scheduled",
    promotion_label: str | None = None,
    promotion_discount_percent: int | None = None,
) -> Trip:
    trip = db.execute(
        select(Trip).where(
            Trip.driver_id == driver.id,
            Trip.departure_province == departure_province,
            Trip.destination_province == destination_province,
            Trip.departure_time == departure_time,
        )
    ).scalar_one_or_none()
    if trip is None:
        trip = Trip(
            driver_id=driver.id,
            vehicle_id=vehicle.id,
            departure_province=departure_province,
            destination_province=destination_province,
            departure_time=departure_time,
            departure_lat=departure_lat,
            departure_lng=departure_lng,
            live_heading=live_heading,
            live_speed_kph=live_speed_kph,
            live_location_updated_at=live_location_updated_at,
            live_location_expires_at=live_location_expires_at,
            auto_repeat_weekly=auto_repeat_weekly,
            recurring_day_of_week=recurring_day_of_week,
            recurring_departure_time=recurring_departure_time,
            price_per_seat=price_per_seat,
            total_seats=total_seats,
            available_seats=available_seats,
            status=status,
            promotion_label=promotion_label,
            promotion_discount_percent=promotion_discount_percent,
        )
        db.add(trip)
        db.flush()
        return trip

    trip.vehicle_id = vehicle.id
    trip.departure_lat = departure_lat
    trip.departure_lng = departure_lng
    trip.live_heading = live_heading
    trip.live_speed_kph = live_speed_kph
    trip.live_location_updated_at = live_location_updated_at
    trip.live_location_expires_at = live_location_expires_at
    trip.auto_repeat_weekly = auto_repeat_weekly
    trip.recurring_day_of_week = recurring_day_of_week
    trip.recurring_departure_time = recurring_departure_time
    trip.price_per_seat = price_per_seat
    trip.total_seats = total_seats
    trip.available_seats = available_seats
    trip.status = status
    trip.promotion_label = promotion_label
    trip.promotion_discount_percent = promotion_discount_percent
    db.flush()
    return trip


def get_or_create_booking(
    db,
    *,
    trip: Trip,
    passenger: User,
    seat_numbers: list[int],
    total_price: Decimal,
    status: str,
    payment_method: str = "cash_on_arrival",
    payment_status: str = "pending",
    pickup_status: str = "pending",
    driver_arrived_at: datetime | None = None,
    driver_requested_boarding_at: datetime | None = None,
    passenger_confirmed_boarding_at: datetime | None = None,
    boarding_confirmation_expires_at: datetime | None = None,
) -> Booking:
    booking = db.execute(select(Booking).where(Booking.trip_id == trip.id, Booking.passenger_id == passenger.id)).scalar_one_or_none()
    if booking is None:
        booking = Booking(
            trip_id=trip.id,
            passenger_id=passenger.id,
            seat_numbers=seat_numbers,
            total_price=total_price,
            status=status,
            payment_method=payment_method,
            payment_status=payment_status,
            pickup_status=pickup_status,
            driver_arrived_at=driver_arrived_at,
            driver_requested_boarding_at=driver_requested_boarding_at,
            passenger_confirmed_boarding_at=passenger_confirmed_boarding_at,
            boarding_confirmation_expires_at=boarding_confirmation_expires_at,
        )
        db.add(booking)
        db.flush()
        return booking
    booking.seat_numbers = seat_numbers
    booking.total_price = total_price
    booking.status = status
    booking.payment_method = payment_method
    booking.payment_status = payment_status
    booking.pickup_status = pickup_status
    booking.driver_arrived_at = driver_arrived_at
    booking.driver_requested_boarding_at = driver_requested_boarding_at
    booking.passenger_confirmed_boarding_at = passenger_confirmed_boarding_at
    booking.boarding_confirmation_expires_at = boarding_confirmation_expires_at
    db.flush()
    return booking


def get_or_create_payment(db, *, booking: Booking, transaction_id: str, payment_method: str, amount: Decimal, status: str, paid_at: datetime | None) -> Payment:
    payment = db.execute(select(Payment).where(Payment.transaction_id == transaction_id)).scalar_one_or_none()
    if payment is None:
        payment = Payment(booking_id=booking.id, transaction_id=transaction_id, payment_method=payment_method, amount=amount, status=status, paid_at=paid_at)
        db.add(payment)
        db.flush()
        return payment
    payment.booking_id = booking.id
    payment.payment_method = payment_method
    payment.amount = amount
    payment.status = status
    payment.paid_at = paid_at
    db.flush()
    return payment


def get_or_create_passenger_place(db, *, user: User, key: str, label: str, address_line: str, lat: Decimal, lng: Decimal, note: str | None = None) -> PassengerQuickPlace:
    place = db.execute(select(PassengerQuickPlace).where(PassengerQuickPlace.user_id == user.id, PassengerQuickPlace.key == key)).scalar_one_or_none()
    if place is None:
        place = PassengerQuickPlace(user_id=user.id, key=key, label=label, address_line=address_line, lat=lat, lng=lng, note=note)
        db.add(place)
        db.flush()
        return place
    place.label = label
    place.address_line = address_line
    place.lat = lat
    place.lng = lng
    place.note = note
    db.flush()
    return place


def get_or_create_runtime_settings(db) -> AppRuntimeSetting:
    settings = db.execute(select(AppRuntimeSetting).where(AppRuntimeSetting.id == 1)).scalar_one_or_none()
    if settings is None:
        settings = AppRuntimeSetting(
            id=1,
            enable_digital_payment=True,
            auto_lock_on_limit=True,
            driver_cash_debt_limit_usd=Decimal("20.00"),
            driver_cash_debt_limit_khr=80000,
        )
        db.add(settings)
    settings.enable_digital_payment = True
    settings.auto_lock_on_limit = True
    settings.driver_cash_debt_limit_usd = Decimal("20.00")
    settings.driver_cash_debt_limit_khr = 80000
    db.flush()
    return settings


def get_or_create_driver_membership(
    db,
    *,
    driver: User,
    code: str,
    label: str,
    service_fee_per_passenger_usd: Decimal,
    service_fee_per_passenger_khr: int,
    monthly_subscription_usd: Decimal,
    monthly_subscription_khr: int,
    verified_badge: bool,
    priority_bookings: bool,
    started_at: datetime,
    next_billing_at: datetime | None,
) -> DriverMembership:
    membership = db.execute(
        select(DriverMembership)
        .where(DriverMembership.driver_id == driver.id, DriverMembership.code == code)
        .order_by(DriverMembership.started_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    if membership is None:
        membership = DriverMembership(driver_id=driver.id, code=code)
        db.add(membership)
    membership.label = label
    membership.status = "active"
    membership.verified_badge = verified_badge
    membership.priority_bookings = priority_bookings
    membership.monthly_subscription_usd = monthly_subscription_usd
    membership.monthly_subscription_khr = monthly_subscription_khr
    membership.service_fee_per_passenger_usd = service_fee_per_passenger_usd
    membership.service_fee_per_passenger_khr = service_fee_per_passenger_khr
    membership.started_at = started_at
    membership.ends_at = None
    membership.next_billing_at = next_billing_at
    membership.auto_renew = True
    db.flush()
    return membership


def get_or_create_driver_wallet(
    db,
    *,
    driver: User,
    service_fee_owed_usd: Decimal,
    service_fee_owed_khr: int,
    subscription_fee_owed_usd: Decimal,
    subscription_fee_owed_khr: int,
    credit_limit_usd: Decimal,
    credit_limit_khr: int,
    is_locked: bool = False,
    locked_reason: str | None = None,
    last_entry_posted_at: datetime | None = None,
    last_settled_at: datetime | None = None,
) -> DriverWallet:
    wallet = db.execute(select(DriverWallet).where(DriverWallet.driver_id == driver.id)).scalar_one_or_none()
    if wallet is None:
        wallet = DriverWallet(driver_id=driver.id)
        db.add(wallet)
    wallet.service_fee_owed_usd = service_fee_owed_usd
    wallet.service_fee_owed_khr = service_fee_owed_khr
    wallet.subscription_fee_owed_usd = subscription_fee_owed_usd
    wallet.subscription_fee_owed_khr = subscription_fee_owed_khr
    wallet.total_owed_usd = service_fee_owed_usd + subscription_fee_owed_usd
    wallet.total_owed_khr = service_fee_owed_khr + subscription_fee_owed_khr
    wallet.credit_limit_usd = credit_limit_usd
    wallet.credit_limit_khr = credit_limit_khr
    wallet.is_locked = is_locked
    wallet.locked_reason = locked_reason
    wallet.last_entry_posted_at = last_entry_posted_at
    wallet.last_settled_at = last_settled_at
    db.flush()
    return wallet


def snapshot_booking_fee(
    booking: Booking,
    *,
    membership: DriverMembership,
    posted_at: datetime,
) -> tuple[Decimal, int]:
    passenger_count = len(booking.seat_numbers or [])
    service_fee_usd = Decimal(str(membership.service_fee_per_passenger_usd)) * passenger_count
    service_fee_khr = int(membership.service_fee_per_passenger_khr) * passenger_count
    booking.membership_code_snapshot = membership.code
    booking.membership_label_snapshot = membership.label
    booking.service_fee_per_passenger_usd = membership.service_fee_per_passenger_usd
    booking.service_fee_per_passenger_khr = membership.service_fee_per_passenger_khr
    booking.service_fee_total_usd = service_fee_usd
    booking.service_fee_total_khr = service_fee_khr
    booking.fee_snapshotted_at = posted_at
    booking.settlement_summary_date = posted_at.date()
    return service_fee_usd, service_fee_khr


def get_or_create_driver_wallet_entry(
    db,
    *,
    driver: User,
    trip: Trip,
    booking: Booking,
    membership: DriverMembership,
    service_fee_usd: Decimal,
    service_fee_khr: int,
    cash_collected_khr: int,
    posted_at: datetime,
    status: str = "owed",
) -> DriverWalletEntry:
    entry = db.execute(select(DriverWalletEntry).where(DriverWalletEntry.booking_id == booking.id)).scalar_one_or_none()
    if entry is None:
        entry = DriverWalletEntry(driver_id=driver.id, trip_id=trip.id, booking_id=booking.id)
        db.add(entry)
    entry.entry_type = "trip_service_fee"
    entry.payment_method = booking.payment_method
    entry.membership_code_snapshot = membership.code
    entry.membership_label_snapshot = membership.label
    entry.passenger_count = len(booking.seat_numbers or [])
    entry.cash_collected_khr = cash_collected_khr
    entry.service_fee_usd = service_fee_usd
    entry.service_fee_khr = service_fee_khr
    entry.status = status
    entry.posted_at = posted_at
    entry.settled_at = None
    entry.notes = "Demo completed trip service-fee debt."
    db.flush()
    return entry


def get_or_create_daily_fee_summary(
    db,
    *,
    driver: User,
    membership: DriverMembership,
    summary_date: date,
    completed_bookings: int,
    confirmed_passengers: int,
    service_fee_usd: Decimal,
    service_fee_khr: int,
    invoice_status: str = "pending",
) -> DriverDailyFeeSummary:
    summary = db.execute(
        select(DriverDailyFeeSummary).where(
            DriverDailyFeeSummary.driver_id == driver.id,
            DriverDailyFeeSummary.summary_date == summary_date,
        )
    ).scalar_one_or_none()
    if summary is None:
        summary = DriverDailyFeeSummary(driver_id=driver.id, summary_date=summary_date)
        db.add(summary)
    summary.membership_id = membership.id
    summary.membership_code = membership.code
    summary.membership_label = membership.label
    summary.completed_bookings = completed_bookings
    summary.confirmed_passengers = confirmed_passengers
    summary.service_fee_usd = service_fee_usd
    summary.service_fee_khr = service_fee_khr
    summary.invoice_status = invoice_status
    db.flush()
    return summary


def get_or_create_driver_invoice(
    db,
    *,
    driver: User,
    membership: DriverMembership,
    daily_summary: DriverDailyFeeSummary,
    invoice_type: str,
    status: str,
    period_start: date,
    period_end: date,
    period_label: str,
    total_usd: Decimal,
    total_khr: int,
    issued_at: datetime,
    due_at: datetime,
) -> DriverInvoice:
    invoice = db.execute(
        select(DriverInvoice).where(
            DriverInvoice.driver_id == driver.id,
            DriverInvoice.type == invoice_type,
            DriverInvoice.period_label == period_label,
        )
    ).scalar_one_or_none()
    if invoice is None:
        invoice = DriverInvoice(driver_id=driver.id, type=invoice_type, period_label=period_label)
        db.add(invoice)
    invoice.membership_id = membership.id
    invoice.daily_summary_id = daily_summary.id
    invoice.status = status
    invoice.period_start = period_start
    invoice.period_end = period_end
    invoice.total_usd = total_usd
    invoice.total_khr = total_khr
    invoice.issued_at = issued_at
    invoice.due_at = due_at
    invoice.paid_at = None
    db.flush()
    return invoice


def upsert_system_ad(
    db,
    *,
    title: str,
    title_kh: str,
    image_url: str,
    link_url: str | None,
    description: str | None,
    description_kh: str | None,
    is_active: bool,
) -> SystemAd:
    ad = db.execute(select(SystemAd).where(SystemAd.title == title)).scalars().first()
    if ad is None:
        ad = SystemAd(title=title, title_kh=title_kh, image_url=image_url)
        db.add(ad)
    ad.title_kh = title_kh
    ad.image_url = image_url
    ad.link_url = link_url
    ad.description = description
    ad.description_kh = description_kh
    ad.is_active = is_active
    db.flush()
    return ad


def upsert_system_discount_ticket(
    db,
    *,
    code: str,
    title: str,
    title_kh: str,
    discount_percent: int,
    description: str | None,
    description_kh: str | None,
    is_active: bool,
    expires_at: datetime,
) -> SystemDiscountTicket:
    ticket = db.execute(
        select(SystemDiscountTicket).where(SystemDiscountTicket.code == code)
    ).scalars().first()
    if ticket is None:
        ticket = SystemDiscountTicket(code=code)
        db.add(ticket)
    ticket.title = title
    ticket.title_kh = title_kh
    ticket.discount_percent = discount_percent
    ticket.description = description
    ticket.description_kh = description_kh
    ticket.is_active = is_active
    ticket.expires_at = expires_at
    db.flush()
    return ticket


def split_seat_numbers(seat_numbers: list[int]) -> list[list[int]]:
    if len(seat_numbers) <= 2:
        return [seat_numbers]
    midpoint = len(seat_numbers) // 2
    return [seat_numbers[:midpoint], seat_numbers[midpoint:]]


def seed() -> None:
    with SessionLocal() as db:
        # Keep seeded datetimes aligned with frontend's Asia/Phnom_Penh time window filtering.
        now = datetime.now(ZoneInfo("Asia/Phnom_Penh")).replace(tzinfo=None, second=0, microsecond=0)
        rng = Random(20260525)

        get_or_create_runtime_settings(db)

        driver_1 = get_or_create_user(db, phone="012345678", full_name="Sok Dara", role="driver", password="strongpass123", rating_avg=Decimal("4.80"), rating_count=128, completed_trips=240)
        driver_2 = get_or_create_user(db, phone="011223344", full_name="Chan Vireak", role="driver", password="strongpass123", rating_avg=Decimal("4.70"), rating_count=96, completed_trips=188)
        passenger_1 = get_or_create_user(db, phone="099887766", full_name="Nary Srey", role="passenger", password="strongpass123")
        passenger_2 = get_or_create_user(db, phone="088776655", full_name="Pich Makara", role="passenger", password="strongpass123")

        prius = get_or_create_vehicle(db, owner=driver_1, plate_number="2AB-1234", seat_type=4, model="Toyota Prius", company_name="Dara Taxi", vehicle_type="Sedan", color="White")
        hiace = get_or_create_vehicle(db, owner=driver_2, plate_number="2CD-5678", seat_type=15, model="Toyota Hiace", company_name="Vireak Van", vehicle_type="Van", color="Silver")

        trip_1_time = now + timedelta(hours=2)
        trip_1 = get_or_create_trip(
            db,
            driver=driver_1,
            vehicle=prius,
            departure_province="ភ្នំពេញ",
            destination_province="ព្រៃវែង",
            departure_time=trip_1_time,
            departure_lat=Decimal("11.573100"),
            departure_lng=Decimal("104.893500"),
            live_heading=85,
            live_speed_kph=Decimal("34.00"),
            live_location_updated_at=now,
            live_location_expires_at=trip_1_time + timedelta(hours=24),
            auto_repeat_weekly=True,
            recurring_day_of_week=trip_1_time.weekday(),
            recurring_departure_time=trip_1_time.time().replace(second=0, microsecond=0),
            price_per_seat=Decimal("8.00"),
            total_seats=4,
            available_seats=2,
            status="active",
            promotion_label="Promo fare",
            promotion_discount_percent=10,
        )

        trip_2_time = now + timedelta(hours=5)
        trip_2 = get_or_create_trip(
            db,
            driver=driver_2,
            vehicle=hiace,
            departure_province="ភ្នំពេញ",
            destination_province="សៀមរាប",
            departure_time=trip_2_time,
            departure_lat=Decimal("11.556200"),
            departure_lng=Decimal("104.928300"),
            live_heading=120,
            live_speed_kph=Decimal("28.50"),
            live_location_updated_at=now,
            live_location_expires_at=trip_2_time + timedelta(hours=24),
            auto_repeat_weekly=False,
            recurring_day_of_week=None,
            recurring_departure_time=None,
            price_per_seat=Decimal("15.00"),
            total_seats=15,
            available_seats=11,
            status="active",
        )

        # Ensure upcoming scheduled options exist from "now" for frontend datetime window tests.
        evening_test_offsets = [25, 70, 115, 160]
        for dep_time in [now + timedelta(minutes=offset) for offset in evening_test_offsets]:
            get_or_create_trip(
                db,
                driver=driver_2,
                vehicle=hiace,
                departure_province="ភ្នំពេញ",
                destination_province="សៀមរាប",
                departure_time=dep_time,
                departure_lat=Decimal("11.556200"),
                departure_lng=Decimal("104.928300"),
                live_heading=None,
                live_speed_kph=None,
                live_location_updated_at=None,
                live_location_expires_at=dep_time + timedelta(hours=24),
                auto_repeat_weekly=False,
                recurring_day_of_week=None,
                recurring_departure_time=None,
                price_per_seat=Decimal("15.00"),
                total_seats=15,
                available_seats=11,
                status="scheduled",
            )

        get_or_create_trip(
            db,
            driver=driver_2,
            vehicle=hiace,
            departure_province="បាត់ដំបង",
            destination_province="ភ្នំពេញ",
            departure_time=now + timedelta(days=1, hours=3),
            departure_lat=Decimal("13.100000"),
            departure_lng=Decimal("103.200000"),
            live_heading=None,
            live_speed_kph=None,
            live_location_updated_at=None,
            live_location_expires_at=now + timedelta(hours=24),
            auto_repeat_weekly=False,
            recurring_day_of_week=None,
            recurring_departure_time=None,
            price_per_seat=Decimal("12.50"),
            total_seats=15,
            available_seats=15,
            status="scheduled",
        )

        booking = get_or_create_booking(
            db,
            trip=trip_1,
            passenger=passenger_1,
            seat_numbers=[1, 2],
            total_price=Decimal("14.40"),
            status="confirmed",
            payment_method="khqr",
            payment_status="paid",
        )
        get_or_create_payment(db, booking=booking, transaction_id="DEMO-TX-0001", payment_method="aba_payway", amount=Decimal("14.40"), status="success", paid_at=now)
        wallet_demo_booking = get_or_create_booking(
            db,
            trip=trip_2,
            passenger=passenger_2,
            seat_numbers=[3, 4, 5, 6],
            total_price=Decimal("60.00"),
            status="confirmed",
            payment_method="cash_on_arrival",
            payment_status="postpaid",
            pickup_status="completed",
            driver_arrived_at=now - timedelta(minutes=50),
            driver_requested_boarding_at=now - timedelta(minutes=45),
            passenger_confirmed_boarding_at=now - timedelta(minutes=42),
            boarding_confirmation_expires_at=now - timedelta(minutes=35),
        )

        demo_membership = get_or_create_driver_membership(
            db,
            driver=driver_2,
            code="pro",
            label="Membership Pro",
            service_fee_per_passenger_usd=Decimal("0.50"),
            service_fee_per_passenger_khr=2000,
            monthly_subscription_usd=Decimal("50.00"),
            monthly_subscription_khr=200000,
            verified_badge=True,
            priority_bookings=True,
            started_at=now - timedelta(days=12),
            next_billing_at=now + timedelta(days=18),
        )
        service_fee_usd, service_fee_khr = snapshot_booking_fee(
            wallet_demo_booking,
            membership=demo_membership,
            posted_at=now - timedelta(minutes=30),
        )
        get_or_create_driver_wallet_entry(
            db,
            driver=driver_2,
            trip=trip_2,
            booking=wallet_demo_booking,
            membership=demo_membership,
            service_fee_usd=service_fee_usd,
            service_fee_khr=service_fee_khr,
            cash_collected_khr=240000,
            posted_at=now - timedelta(minutes=30),
        )
        fee_summary = get_or_create_daily_fee_summary(
            db,
            driver=driver_2,
            membership=demo_membership,
            summary_date=now.date(),
            completed_bookings=1,
            confirmed_passengers=len(wallet_demo_booking.seat_numbers),
            service_fee_usd=service_fee_usd,
            service_fee_khr=service_fee_khr,
        )
        get_or_create_driver_invoice(
            db,
            driver=driver_2,
            membership=demo_membership,
            daily_summary=fee_summary,
            invoice_type="service_fee",
            status="issued",
            period_start=now.date(),
            period_end=now.date(),
            period_label=now.strftime("Demo service fees %Y-%m-%d"),
            total_usd=service_fee_usd,
            total_khr=service_fee_khr,
            issued_at=now - timedelta(minutes=20),
            due_at=now + timedelta(days=1),
        )
        get_or_create_driver_wallet(
            db,
            driver=driver_2,
            service_fee_owed_usd=service_fee_usd,
            service_fee_owed_khr=service_fee_khr,
            subscription_fee_owed_usd=Decimal("0.00"),
            subscription_fee_owed_khr=0,
            credit_limit_usd=Decimal("20.00"),
            credit_limit_khr=80000,
            last_entry_posted_at=now - timedelta(minutes=30),
        )

        get_or_create_passenger_place(db, user=passenger_1, key="home", label="Home", address_line="Street 2004, Toul Kork, Phnom Penh", lat=Decimal("11.573700"), lng=Decimal("104.892900"), note="Near TK Avenue")
        get_or_create_passenger_place(db, user=passenger_1, key="work", label="Work", address_line="Monivong Blvd, Daun Penh, Phnom Penh", lat=Decimal("11.562900"), lng=Decimal("104.918800"), note="Office area")

        tomorrow_driver = get_or_create_user(
            db,
            phone="010202526",
            full_name="Tomorrow Seat Demo Driver",
            role="driver",
            password="strongpass123",
            is_verified=True,
            rating_avg=Decimal("4.90"),
            rating_count=212,
            completed_trips=420,
        )
        tomorrow_passengers = [
            get_or_create_user(db, phone=f"09877{idx:04d}", full_name=f"Seat Demo Passenger {idx}", role="passenger", password="strongpass123")
            for idx in range(1, 7)
        ]
        province_route_passengers = [
            get_or_create_user(db, phone=f"09766{idx:04d}", full_name=f"Province Route Passenger {idx}", role="passenger", password="strongpass123")
            for idx in range(1, 19)
        ]
        tomorrow = (now + timedelta(days=1)).date()
        tomorrow_specs = [
            {
                "plate": "2SD-4004",
                "seat_type": 4,
                "model": "Toyota Highlander",
                "vehicle_type": "SUV",
                "color": "White",
                "departure_time": datetime.combine(tomorrow, time(8, 30)),
                "booked": [1],
                "price": Decimal("55000.00"),
                "promo": 10,
            },
            {
                "plate": "2SD-4015",
                "seat_type": 15,
                "model": "Toyota Hiace",
                "vehicle_type": "Van",
                "color": "Silver",
                "departure_time": datetime.combine(tomorrow, time(10, 15)),
                "booked": [1, 2, 7, 8, 15],
                "price": Decimal("35000.00"),
                "promo": None,
            },
            {
                "plate": "2SD-4016",
                "seat_type": 16,
                "model": "Hyundai H-1",
                "vehicle_type": "Van",
                "color": "Black",
                "departure_time": datetime.combine(tomorrow, time(11, 45)),
                "booked": [1, 2, 5, 6, 16],
                "price": Decimal("38000.00"),
                "promo": None,
            },
            {
                "plate": "2SD-4023",
                "seat_type": 23,
                "model": "Hyundai Universe Sleeper",
                "vehicle_type": "Sleeping Bus",
                "color": "Gold",
                "departure_time": datetime.combine(tomorrow, time(21, 30)),
                "booked": [1, 2, 3, 9, 10, 11, 20, 21],
                "price": Decimal("45000.00"),
                "promo": 12,
            },
            {
                "plate": "2SD-4030",
                "seat_type": 30,
                "model": "Toyota Coaster",
                "vehicle_type": "Mini Bus",
                "color": "Blue",
                "departure_time": datetime.combine(tomorrow, time(13, 45)),
                "booked": [1, 2, 3, 10, 11, 12, 20, 21],
                "price": Decimal("30000.00"),
                "promo": 15,
            },
            {
                "plate": "2SD-4045",
                "seat_type": 45,
                "model": "Hyundai Universe",
                "vehicle_type": "Bus",
                "color": "Red",
                "departure_time": datetime.combine(tomorrow, time(16, 30)),
                "booked": [1, 2, 3, 4, 5, 12, 13, 14, 24, 25, 26, 40, 41],
                "price": Decimal("25000.00"),
                "promo": None,
            },
        ]
        for index, spec in enumerate(tomorrow_specs):
            vehicle = get_or_create_vehicle(
                db,
                owner=tomorrow_driver,
                plate_number=spec["plate"],
                seat_type=spec["seat_type"],
                model=spec["model"],
                company_name="Seat Demo Transit",
                vehicle_type=spec["vehicle_type"],
                color=spec["color"],
            )
            booked_seats = spec["booked"]
            trip = get_or_create_trip(
                db,
                driver=tomorrow_driver,
                vehicle=vehicle,
                departure_province="ភ្នំពេញ",
                destination_province="ព្រៃវែង",
                departure_time=spec["departure_time"],
                departure_lat=Decimal("11.556400") + Decimal(str(index * 0.003)),
                departure_lng=Decimal("104.928200") + Decimal(str(index * 0.003)),
                live_heading=90 + index * 20,
                live_speed_kph=Decimal("32.00") + Decimal(str(index)),
                live_location_updated_at=now,
                live_location_expires_at=spec["departure_time"] + timedelta(hours=24),
                auto_repeat_weekly=False,
                recurring_day_of_week=None,
                recurring_departure_time=None,
                price_per_seat=spec["price"],
                total_seats=spec["seat_type"],
                available_seats=spec["seat_type"] - len(booked_seats),
                status="scheduled",
                promotion_label="Promo fare" if spec["promo"] else None,
                promotion_discount_percent=spec["promo"],
            )
            if booked_seats:
                get_or_create_booking(
                    db,
                    trip=trip,
                    passenger=tomorrow_passengers[index],
                    seat_numbers=booked_seats,
                    total_price=spec["price"] * Decimal(len(booked_seats)),
                    status="confirmed",
                    payment_method="khqr" if index % 2 == 0 else "cash_on_arrival",
                )

        phnom_penh_departure_lat = Decimal("11.556400")
        phnom_penh_departure_lng = Decimal("104.928200")
        non_phnom_penh_provinces = [province for province in PROVINCES if province != "ភ្នំពេញ"]
        outbound_times = {
            4: time(6, 30),
            15: time(8, 0),
            16: time(10, 0),
            23: time(12, 30),
            30: time(15, 0),
            45: time(18, 30),
        }
        inbound_times = {
            4: time(7, 45),
            15: time(9, 30),
            16: time(11, 15),
            23: time(14, 15),
            30: time(17, 15),
            45: time(21, 0),
        }

        # Build province coverage in both directions so frontend searches can test each province and each seat layout.
        for province_index, province in enumerate(non_phnom_penh_provinces, start=1):
            province_lat = Decimal("10.800000") + Decimal(str(province_index * 0.085))
            province_lng = Decimal("102.700000") + Decimal(str(province_index * 0.095))

            for seat_index, seat_type in enumerate(SEAT_TYPE_SPECS, start=1):
                spec = SEAT_TYPE_SPECS[seat_type]
                driver = get_or_create_user(
                    db,
                    phone=f"066{province_index:02d}{seat_type:02d}9",
                    full_name=f"{province} Route Driver {seat_type}",
                    role="driver",
                    password="strongpass123",
                    is_verified=True,
                    rating_avg=Decimal("4.20") + Decimal(str((province_index + seat_index) % 7)) / Decimal("10"),
                    rating_count=50 + (province_index * 4) + seat_index,
                    completed_trips=90 + (province_index * 7) + (seat_index * 5),
                )
                vehicle = get_or_create_vehicle(
                    db,
                    owner=driver,
                    plate_number=f"2RT-{province_index:02d}{seat_type:02d}",
                    seat_type=seat_type,
                    model=spec["model"],
                    company_name=f"{province} Express",
                    vehicle_type=spec["vehicle_type"],
                    color=spec["color"],
                )

                price_delta = Decimal(str((province_index % 4) * 2500))
                base_price = spec["price"] + price_delta
                promotion_discount = 10 if province_index % 3 == 0 else None
                promotion_label = "Promo fare" if promotion_discount else None

                outbound_departure_time = datetime.combine(tomorrow, outbound_times[seat_type]) + timedelta(minutes=province_index)
                inbound_departure_time = datetime.combine(tomorrow, inbound_times[seat_type]) + timedelta(minutes=province_index)

                outbound_booked_count = min(spec["booked_count"] + (province_index % 2), seat_type - 1)
                outbound_booked_seats = sorted(rng.sample(range(1, seat_type + 1), k=outbound_booked_count))
                outbound_trip = get_or_create_trip(
                    db,
                    driver=driver,
                    vehicle=vehicle,
                    departure_province="ភ្នំពេញ",
                    destination_province=province,
                    departure_time=outbound_departure_time,
                    departure_lat=phnom_penh_departure_lat + Decimal(str(province_index * 0.001)),
                    departure_lng=phnom_penh_departure_lng + Decimal(str(province_index * 0.001)),
                    live_heading=60 + (seat_index * 18),
                    live_speed_kph=Decimal("24.00") + Decimal(str(seat_index)),
                    live_location_updated_at=now,
                    live_location_expires_at=outbound_departure_time + timedelta(hours=24),
                    auto_repeat_weekly=False,
                    recurring_day_of_week=None,
                    recurring_departure_time=None,
                    price_per_seat=base_price,
                    total_seats=seat_type,
                    available_seats=seat_type - len(outbound_booked_seats),
                    status="scheduled",
                    promotion_label=promotion_label,
                    promotion_discount_percent=promotion_discount,
                )
                for split_index, seat_numbers in enumerate(split_seat_numbers(outbound_booked_seats)):
                    if not seat_numbers:
                        continue
                    passenger = province_route_passengers[(province_index + seat_index + split_index) % len(province_route_passengers)]
                    get_or_create_booking(
                        db,
                        trip=outbound_trip,
                        passenger=passenger,
                        seat_numbers=seat_numbers,
                        total_price=base_price * Decimal(len(seat_numbers)),
                        status="confirmed" if split_index == 0 else "pending",
                        payment_method="khqr" if split_index == 0 else "cash_on_arrival",
                    )

                inbound_booked_count = min(spec["booked_count"] + ((province_index + 1) % 3), seat_type - 1)
                inbound_booked_seats = sorted(rng.sample(range(1, seat_type + 1), k=inbound_booked_count))
                inbound_trip = get_or_create_trip(
                    db,
                    driver=driver,
                    vehicle=vehicle,
                    departure_province=province,
                    destination_province="ភ្នំពេញ",
                    departure_time=inbound_departure_time,
                    departure_lat=province_lat,
                    departure_lng=province_lng,
                    live_heading=90 + (seat_index * 12),
                    live_speed_kph=Decimal("22.00") + Decimal(str(seat_index)),
                    live_location_updated_at=now,
                    live_location_expires_at=inbound_departure_time + timedelta(hours=24),
                    auto_repeat_weekly=False,
                    recurring_day_of_week=None,
                    recurring_departure_time=None,
                    price_per_seat=base_price + Decimal("1500.00"),
                    total_seats=seat_type,
                    available_seats=seat_type - len(inbound_booked_seats),
                    status="scheduled",
                    promotion_label=promotion_label,
                    promotion_discount_percent=promotion_discount,
                )
                for split_index, seat_numbers in enumerate(split_seat_numbers(inbound_booked_seats)):
                    if not seat_numbers:
                        continue
                    passenger = province_route_passengers[(province_index + seat_index + split_index + 3) % len(province_route_passengers)]
                    get_or_create_booking(
                        db,
                        trip=inbound_trip,
                        passenger=passenger,
                        seat_numbers=seat_numbers,
                        total_price=(base_price + Decimal("1500.00")) * Decimal(len(seat_numbers)),
                        status="confirmed" if split_index == 0 else "pending",
                        payment_method="cash_on_arrival" if split_index == 0 else "khqr",
                    )

        phnom_penh_streets = ["Street 2004", "Street 271", "Street 182", "Street 315", "Street 598", "Street 360", "Street 51", "Street 93", "Street 278", "Street 432"]
        kh_districts = ["ទួលគោក", "ចំការមន", "ដូនពេញ", "សែនសុខ", "មានជ័យ"]
        vehicle_models = ["Prius", "Hiace", "Hyundai H-1", "Hyundai Universe Sleeper", "Hyundai County", "Toyota Coaster"]
        seat_types = [4, 15, 16, 23, 30, 45]
        destinations = non_phnom_penh_provinces
        vehicle_type_by_seat = {
            4: "Car",
            15: "Van",
            16: "Van",
            23: "Sleeping Bus",
            30: "Mini Bus",
            45: "Bus",
        }

        for i in range(1, 51):
            street = phnom_penh_streets[(i - 1) % len(phnom_penh_streets)]
            district = kh_districts[(i - 1) % len(kh_districts)]
            model = vehicle_models[(i - 1) % len(vehicle_models)]
            seat_type = seat_types[(i - 1) % len(seat_types)]
            destination = destinations[(i - 1) % len(destinations)]

            driver = get_or_create_user(
                db,
                phone=f"07055{i:04d}",
                full_name=f"Phnom Penh Driver {i:02d}",
                role="driver",
                password="strongpass123",
                is_verified=True,
                rating_avg=Decimal("4.20") + Decimal(str((i % 8) / 10)),
                rating_count=40 + (i * 3),
                completed_trips=80 + (i * 5),
            )
            vehicle = get_or_create_vehicle(
                db,
                owner=driver,
                plate_number=f"2PP-{3000 + i}",
                seat_type=seat_type,
                model=model,
                company_name=f"{street} Transit",
                vehicle_type=vehicle_type_by_seat[seat_type],
                color=["White", "Black", "Silver", "Blue", "Red"][(i - 1) % 5],
            )

            departure_time = now + timedelta(hours=(1 + (i % 8)), minutes=(i * 7) % 60)
            total_seats = seat_type
            available = total_seats - rng.randint(0, max(1, total_seats // 3))
            lat = Decimal("11.520000") + Decimal(str((i % 30) * 0.0031))
            lng = Decimal("104.860000") + Decimal(str((i % 30) * 0.0027))
            auto_repeat = (i % 3 == 0)

            get_or_create_trip(
                db,
                driver=driver,
                vehicle=vehicle,
                departure_province="ភ្នំពេញ",
                destination_province=destination,
                departure_time=departure_time,
                departure_lat=lat,
                departure_lng=lng,
                live_heading=(45 + (i % 180)),
                live_speed_kph=Decimal(str(20 + (i % 25))),
                live_location_updated_at=now - timedelta(minutes=(i % 20)),
                live_location_expires_at=departure_time + timedelta(hours=24),
                auto_repeat_weekly=auto_repeat,
                recurring_day_of_week=departure_time.weekday() if auto_repeat else None,
                recurring_departure_time=departure_time.time().replace(second=0, microsecond=0) if auto_repeat else None,
                price_per_seat=Decimal("6.50") + Decimal(str(i % 6)),
                total_seats=total_seats,
                available_seats=available,
                status="active" if i <= 10 else "scheduled",
                promotion_label="Promo fare" if destination == "ព្រៃវែង" and i % 2 == 0 else None,
                promotion_discount_percent=10 if destination == "ព្រៃវែង" and i % 2 == 0 else None,
            )

        promo_rows = db.execute(
            select(Trip).where(
                Trip.departure_province == "ភ្នំពេញ",
                Trip.destination_province == "ព្រៃវែង",
                Trip.status == "scheduled",
            )
        ).scalars().all()
        for trip in promo_rows:
            trip.promotion_label = "Promo fare"
            trip.promotion_discount_percent = 10

        # Seed default system ads.
        upsert_system_ad(
            db,
            title="Water Festival Discount",
            title_kh="បុណ្យអុំទូក បញ្ចុះតម្លៃពិសេស",
            image_url="https://images.unsplash.com/photo-1540959733332-eab4deceeaf7?q=80&w=600&auto=format&fit=crop",
            link_url="/travel/promotions",
            description="Get 20% off on all trips during the Water Festival!",
            description_kh="ទទួលបានការបញ្ចុះតម្លៃ ២០% រាល់ការធ្វើដំណើរក្នុងឱកាសបុណ្យអុំទូក!",
            is_active=True,
        )
        upsert_system_ad(
            db,
            title="VIP Member Benefits",
            title_kh="អត្ថប្រយោជន៍សមាជិក VIP",
            image_url="https://images.unsplash.com/photo-1494976388531-d1058494cdd8?q=80&w=600&auto=format&fit=crop",
            link_url="/travel/membership",
            description="Upgrade to VIP for zero commission on your first 10 trips.",
            description_kh="តម្លើងទៅ VIP សម្រាប់កម្រៃជើងសារសូន្យ សម្រាប់ការធ្វើដំណើរ ១០ ដងដំបូង។",
            is_active=True,
        )
        upsert_system_ad(
            db,
            title="Safe Travel with My Travel",
            title_kh="ធ្វើដំណើរដោយសុវត្ថិភាពជាមួយ ម៉ាយ ត្រាវែល",
            image_url="https://images.unsplash.com/photo-1449965408869-eaa3f722e40d?q=80&w=600&auto=format&fit=crop",
            link_url="/travel/safety",
            description="Our drivers are fully vetted and verified for your peace of mind.",
            description_kh="អ្នកបើកបររបស់យើងត្រូវបានត្រួតពិនិត្យ និងផ្ទៀងផ្ទាត់យ៉ាងម៉ត់ចត់បំផុត។",
            is_active=True,
        )

        # Seed default system discount tickets.
        upsert_system_discount_ticket(
            db,
            code="WELCOME15",
            title="New Passenger Promo",
            title_kh="ប្រូម៉ូសិនអ្នកដំណើរថ្មី",
            discount_percent=15,
            description="15% discount for your first intercounty trip",
            description_kh="បញ្ចុះតម្លៃ ១៥% សម្រាប់ការធ្វើដំណើរអន្តរខេត្តលើកដំបូង",
            is_active=True,
            expires_at=now + timedelta(days=90),
        )
        upsert_system_discount_ticket(
            db,
            code="PPTOREP20",
            title="Phnom Penh - Siem Reap Special",
            title_kh="ប្រូម៉ូសិនពិសេស ភ្នំពេញ - សៀមរាប",
            discount_percent=20,
            description="Enjoy 20% discount on Phnom Penh to Siem Reap routes",
            description_kh="រីករាយជាមួយការបញ្ចុះតម្លៃ ២០% លើផ្លូវពីភ្នំពេញទៅសៀមរាប",
            is_active=True,
            expires_at=now + timedelta(days=30),
        )
        upsert_system_discount_ticket(
            db,
            code="KHMERNEWYEAR",
            title="Khmer New Year celebration ticket",
            title_kh="សំបុត្រអបអរសាទរពិធីបុណ្យចូលឆ្នាំខ្មែរ",
            discount_percent=25,
            description="Special 25% discount coupon for family trips",
            description_kh="ប័ណ្ណបញ្ចុះតម្លៃពិសេស ២៥% សម្រាប់ការធ្វើដំណើរជាលក្ខណៈគ្រួសារ",
            is_active=True,
            expires_at=now + timedelta(days=120),
        )

        db.commit()
        print("Demo data ready.")
        print("Driver login: 012345678 / strongpass123")
        print("Driver wallet demo login: 011223344 / strongpass123")
        print("Passenger login: 099887766 / strongpass123")
        print("Added 50 Phnom Penh demo drivers (phones: 070550001 - 070550050)")


if __name__ == "__main__":
    seed()
