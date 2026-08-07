from sqlalchemy import select
from sqlalchemy.orm import Session
from uuid import UUID

from .models import User, Vehicle, Trip, Booking, Payment
from .schemas import ItemCreate, ItemRead, ItemUpdate


class ItemNotFoundError(Exception):
    pass


class ItemService:
    """Legacy ItemService - preserved for existing routes"""
    def list_items(self, db: Session) -> list[ItemRead]:
        # Returning empty list as Item model no longer exists
        return []

    def get_item(self, db: Session, item_id: int) -> ItemRead:
        raise ItemNotFoundError

    def create_item(self, db: Session, item: ItemCreate) -> ItemRead:
        raise ItemNotFoundError

    def update_item(self, db: Session, item_id: int, item: ItemUpdate) -> ItemRead:
        raise ItemNotFoundError

    def delete_item(self, db: Session, item_id: int) -> None:
        raise ItemNotFoundError


# Legacy service instance for backwards compatibility
item_service = ItemService()


# Ride-sharing Services
class UserService:
    def get_user_by_phone(self, db: Session, phone: str) -> User | None:
        return db.execute(select(User).where(User.phone == phone)).scalar()

    def create_user(self, db: Session, phone: str, full_name: str, role: str) -> User:
        user = User(phone=phone, full_name=full_name, role=role)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def get_user(self, db: Session, user_id: UUID) -> User | None:
        return db.get(User, user_id)


class VehicleService:
    def get_vehicle(self, db: Session, vehicle_id: UUID) -> Vehicle | None:
        return db.get(Vehicle, vehicle_id)

    def get_vehicles_by_owner(self, db: Session, owner_id: UUID) -> list[Vehicle]:
        return db.execute(select(Vehicle).where(Vehicle.owner_id == owner_id)).scalars().all()


class TripService:
    def search_trips(self, db: Session, departure: str, destination: str) -> list[Trip]:
        return db.execute(
            select(Trip).where(
                (Trip.departure_province == departure) &
                (Trip.destination_province == destination) &
                (Trip.status == 'scheduled')
            )
        ).scalars().all()

    def get_trip(self, db: Session, trip_id: UUID) -> Trip | None:
        return db.get(Trip, trip_id)


class BookingService:
    def create_booking(self, db: Session, trip_id: UUID, passenger_id: UUID, seat_numbers: list[int], total_price: float) -> Booking:
        booking = Booking(
            trip_id=trip_id,
            passenger_id=passenger_id,
            seat_numbers=seat_numbers,
            total_price=total_price
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)
        return booking

    def get_booking(self, db: Session, booking_id: UUID) -> Booking | None:
        return db.get(Booking, booking_id)


class PaymentService:
    def create_payment(self, db: Session, booking_id: UUID, transaction_id: str, payment_method: str, amount: float) -> Payment:
        payment = Payment(
            booking_id=booking_id,
            transaction_id=transaction_id,
            payment_method=payment_method,
            amount=amount
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment

    def get_payment(self, db: Session, payment_id: UUID) -> Payment | None:
        return db.get(Payment, payment_id)


item_service = ItemService()