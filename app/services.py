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


# Push Notification Service
import logging
import os
from typing import Any
from .models import UserPushToken

logger = logging.getLogger("mytravel.push")

_firebase_app_initialized = False


def _get_firebase_app():
    global _firebase_app_initialized
    if _firebase_app_initialized:
        return True
    try:
        import firebase_admin
        from firebase_admin import credentials
        from pathlib import Path

        backend_root = Path(__file__).resolve().parents[1]
        cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
        resolved_path = None

        if cred_path:
            if os.path.isabs(cred_path) and os.path.exists(cred_path):
                resolved_path = cred_path
            elif (backend_root / cred_path).exists():
                resolved_path = str(backend_root / cred_path)
            elif os.path.exists(cred_path):
                resolved_path = cred_path

        if not resolved_path:
            # Auto-discover any firebase-adminsdk json in backend_repo root
            for candidate in backend_root.glob("*firebase-adminsdk*.json"):
                resolved_path = str(candidate)
                break

        if resolved_path:
            cred = credentials.Certificate(resolved_path)
            firebase_admin.initialize_app(cred)
            _firebase_app_initialized = True
            logger.info("Firebase Admin initialized from %s", resolved_path)
            return True
        elif len(firebase_admin._apps) > 0:
            _firebase_app_initialized = True
            return True
        else:
            try:
                firebase_admin.initialize_app()
                _firebase_app_initialized = True
                logger.info("Firebase Admin initialized with default credentials")
                return True
            except Exception as e:
                logger.debug("Firebase Admin default init skipped: %s", e)
                return False
    except ImportError:
        logger.debug("firebase-admin package not installed; falling back to logged push dispatch")
        return False
    except Exception as e:
        logger.warning("Failed to initialize Firebase Admin: %s", e)
        return False


def send_push_notification_to_user(
    db: Session,
    user_id: UUID | str,
    title: str,
    body: str,
    data: dict[str, Any] | None = None,
    badge_count: int | None = None,
) -> int:
    """
    Sends a push notification to all registered active devices for a given user.
    Returns the number of devices targeted.
    """
    try:
        from sqlalchemy import inspect
        bind = db.get_bind()
        if not inspect(bind).has_table("user_push_tokens"):
            return 0
    except Exception:
        return 0

    if isinstance(user_id, str):
        try:
            target_uid = UUID(user_id)
        except ValueError:
            return 0
    else:
        target_uid = user_id

    try:
        tokens = db.execute(
            select(UserPushToken.push_token)
            .where(UserPushToken.user_id == target_uid)
        ).scalars().all()
    except Exception as e:
        logger.debug("Failed to query user push tokens: %s", e)
        return 0

    if not tokens:
        logger.debug("No push tokens registered for user %s", target_uid)
        return 0

    return send_push_notification_to_tokens(
        tokens=list(tokens),
        title=title,
        body=body,
        data=data,
        badge_count=badge_count,
    )


def send_push_notification_to_tokens(
    tokens: list[str],
    title: str,
    body: str,
    data: dict[str, Any] | None = None,
    badge_count: int | None = None,
) -> int:
    """
    Sends a push notification to a list of FCM device registration tokens.
    """
    if not tokens:
        return 0

    clean_data = {str(k): str(v) for k, v in (data or {}).items() if v is not None}
    clean_data["click_action"] = "FLUTTER_NOTIFICATION_CLICK"

    has_firebase = _get_firebase_app()
    if has_firebase:
        try:
            from firebase_admin import messaging

            android_config = messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    title=title,
                    body=body,
                    sound="default",
                    channel_id="mytravel_channel",
                    priority="max",
                    default_vibrate_timings=True,
                ),
                data=clean_data,
            )
            apns_config = messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        alert=messaging.ApsAlert(title=title, body=body),
                        sound="default",
                        badge=badge_count,
                    )
                )
            )

            messages = [
                messaging.Message(
                    token=token,
                    notification=messaging.Notification(title=title, body=body),
                    data=clean_data,
                    android=android_config,
                    apns=apns_config,
                )
                for token in tokens
            ]
            response = messaging.send_each(messages)
            logger.info(
                "Dispatched FCM push to %d devices: %d successes, %d failures",
                len(tokens),
                response.success_count,
                response.failure_count,
            )
            return response.success_count
        except Exception as e:
            logger.warning("FCM dispatch error: %s", e)

    logger.info(
        "[PUSH NOTIFICATION] Target tokens (%d): Title='%s' Body='%s' Data=%s",
        len(tokens),
        title,
        body,
        clean_data,
    )
    return len(tokens)