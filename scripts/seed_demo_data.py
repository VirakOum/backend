from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
import sys

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.auth import hash_password
from app.db import SessionLocal
from app.models import Booking, Payment, Trip, User, Vehicle


def get_or_create_user(
    db,
    *,
    phone: str,
    full_name: str,
    role: str,
    password: str,
    avatar_url: str | None = None,
    is_verified: bool = True,
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
        )
        db.add(user)
        db.flush()
        return user

    user.full_name = full_name
    user.role = role
    user.password_hash = password_hash
    user.avatar_url = avatar_url
    user.is_verified = is_verified
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
) -> Vehicle:
    vehicle = db.execute(
        select(Vehicle).where(Vehicle.plate_number == plate_number)
    ).scalar_one_or_none()
    if vehicle is None:
        vehicle = Vehicle(
            owner_id=owner.id,
            plate_number=plate_number,
            seat_type=seat_type,
            model=model,
            company_name=company_name,
        )
        db.add(vehicle)
        db.flush()
        return vehicle

    vehicle.owner_id = owner.id
    vehicle.seat_type = seat_type
    vehicle.model = model
    vehicle.company_name = company_name
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
    price_per_seat: Decimal,
    total_seats: int,
    available_seats: int,
    status: str = "scheduled",
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
            price_per_seat=price_per_seat,
            total_seats=total_seats,
            available_seats=available_seats,
            status=status,
        )
        db.add(trip)
        db.flush()
        return trip

    trip.vehicle_id = vehicle.id
    trip.price_per_seat = price_per_seat
    trip.total_seats = total_seats
    trip.available_seats = available_seats
    trip.status = status
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
) -> Booking:
    booking = db.execute(
        select(Booking).where(
            Booking.trip_id == trip.id,
            Booking.passenger_id == passenger.id,
        )
    ).scalar_one_or_none()
    if booking is None:
        booking = Booking(
            trip_id=trip.id,
            passenger_id=passenger.id,
            seat_numbers=seat_numbers,
            total_price=total_price,
            status=status,
        )
        db.add(booking)
        db.flush()
        return booking

    booking.seat_numbers = seat_numbers
    booking.total_price = total_price
    booking.status = status
    db.flush()
    return booking


def get_or_create_payment(
    db,
    *,
    booking: Booking,
    transaction_id: str,
    payment_method: str,
    amount: Decimal,
    status: str,
    paid_at: datetime | None,
) -> Payment:
    payment = db.execute(
        select(Payment).where(Payment.transaction_id == transaction_id)
    ).scalar_one_or_none()
    if payment is None:
        payment = Payment(
            booking_id=booking.id,
            transaction_id=transaction_id,
            payment_method=payment_method,
            amount=amount,
            status=status,
            paid_at=paid_at,
        )
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


def seed() -> None:
    with SessionLocal() as db:
        now = datetime.utcnow().replace(second=0, microsecond=0)

        driver_1 = get_or_create_user(
            db,
            phone="012345678",
            full_name="Sok Dara",
            role="driver",
            password="strongpass123",
        )
        driver_2 = get_or_create_user(
            db,
            phone="011223344",
            full_name="Chan Vireak",
            role="driver",
            password="strongpass123",
        )
        passenger_1 = get_or_create_user(
            db,
            phone="099887766",
            full_name="Nary Srey",
            role="passenger",
            password="strongpass123",
        )
        passenger_2 = get_or_create_user(
            db,
            phone="088776655",
            full_name="Pich Makara",
            role="passenger",
            password="strongpass123",
        )

        prius = get_or_create_vehicle(
            db,
            owner=driver_1,
            plate_number="2AB-1234",
            seat_type=4,
            model="Prius",
            company_name="Dara Taxi",
        )
        hiace = get_or_create_vehicle(
            db,
            owner=driver_2,
            plate_number="2CD-5678",
            seat_type=15,
            model="Hiace",
            company_name="Vireak Van",
        )

        trip_1 = get_or_create_trip(
            db,
            driver=driver_1,
            vehicle=prius,
            departure_province="ភ្នំពេញ",
            destination_province="ព្រៃវែង",
            departure_time=now + timedelta(hours=2),
            price_per_seat=Decimal("8.00"),
            total_seats=4,
            available_seats=2,
        )
        trip_2 = get_or_create_trip(
            db,
            driver=driver_2,
            vehicle=hiace,
            departure_province="ភ្នំពេញ",
            destination_province="សៀមរាប",
            departure_time=now + timedelta(hours=5),
            price_per_seat=Decimal("15.00"),
            total_seats=15,
            available_seats=11,
        )
        get_or_create_trip(
            db,
            driver=driver_2,
            vehicle=hiace,
            departure_province="បាត់ដំបង",
            destination_province="ភ្នំពេញ",
            departure_time=now + timedelta(days=1, hours=3),
            price_per_seat=Decimal("12.50"),
            total_seats=15,
            available_seats=15,
        )

        booking = get_or_create_booking(
            db,
            trip=trip_1,
            passenger=passenger_1,
            seat_numbers=[1, 2],
            total_price=Decimal("16.00"),
            status="confirmed",
        )
        get_or_create_payment(
            db,
            booking=booking,
            transaction_id="DEMO-TX-0001",
            payment_method="aba_payway",
            amount=Decimal("16.00"),
            status="success",
            paid_at=now,
        )

        get_or_create_booking(
            db,
            trip=trip_2,
            passenger=passenger_2,
            seat_numbers=[3, 4, 5, 6],
            total_price=Decimal("60.00"),
            status="pending",
        )

        db.commit()

        print("Demo data ready.")
        print("Driver login: 012345678 / strongpass123")
        print("Passenger login: 099887766 / strongpass123")
        print("Sample routes:")
        print("  - ភ្នំពេញ -> ព្រៃវែង")
        print("  - ភ្នំពេញ -> សៀមរាប")
        print("  - បាត់ដំបង -> ភ្នំពេញ")


if __name__ == "__main__":
    seed()
