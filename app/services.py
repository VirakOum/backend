from sqlalchemy import select, func
from sqlalchemy.orm import Session
from uuid import UUID

from .models import User, Vehicle, VehicleModel, Trip, Booking, Payment, Item
from .schemas import ItemCreate, ItemRead, ItemUpdate


class ItemNotFoundError(Exception):
    pass


class ItemService:
    def list_items(self, db: Session) -> list[Item]:
        return list(db.execute(select(Item).order_by(Item.id.asc())).scalars().all())

    def get_item(self, db: Session, item_id: int) -> Item:
        item = db.get(Item, item_id)
        if not item:
            raise ItemNotFoundError
        return item

    def create_item(self, db: Session, item: ItemCreate) -> Item:
        db_item = Item(name=item.name, description=item.description)
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item

    def update_item(self, db: Session, item_id: int, item: ItemUpdate) -> Item:
        db_item = self.get_item(db, item_id)
        if item.name is not None:
            db_item.name = item.name
        if item.description is not None:
            db_item.description = item.description
        db.commit()
        db.refresh(db_item)
        return db_item

    def delete_item(self, db: Session, item_id: int) -> None:
        db_item = self.get_item(db, item_id)
        db.delete(db_item)
        db.commit()


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


DEFAULT_CAR_MODELS = [
    {"brand": "Toyota", "model_name": "Prius", "display_name": "Toyota Prius", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 1},
    {"brand": "Toyota", "model_name": "Alphard", "display_name": "Toyota Alphard", "vehicle_type": "MPV / Minivan", "seat_count": 7, "sort_order": 2},
    {"brand": "Hyundai", "model_name": "Starex", "display_name": "Hyundai Starex", "vehicle_type": "Minivan", "seat_count": 12, "sort_order": 3},
    {"brand": "Lexus", "model_name": "RX330", "display_name": "Lexus RX330", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 4},
    {"brand": "Toyota", "model_name": "Sienna", "display_name": "Toyota Sienna", "vehicle_type": "Minivan", "seat_count": 7, "sort_order": 5},
    {"brand": "Ford", "model_name": "Everest", "display_name": "Ford Everest", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 6},
    {"brand": "Toyota", "model_name": "HiAce", "display_name": "Toyota HiAce", "vehicle_type": "Van", "seat_count": 15, "sort_order": 7},
    {"brand": "Toyota", "model_name": "Camry", "display_name": "Toyota Camry", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 8},
    {"brand": "Toyota", "model_name": "Fortuner", "display_name": "Toyota Fortuner", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 9},
    {"brand": "Hyundai", "model_name": "H1", "display_name": "Hyundai H1", "vehicle_type": "Van", "seat_count": 12, "sort_order": 10},
    {"brand": "Toyota", "model_name": "Highlander", "display_name": "Toyota Highlander", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 11},
    {"brand": "Toyota", "model_name": "Land Cruiser", "display_name": "Toyota Land Cruiser", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 12},
    {"brand": "Toyota", "model_name": "Land Cruiser Prado", "display_name": "Toyota Land Cruiser Prado", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 13},
    {"brand": "Toyota", "model_name": "Corolla Cross", "display_name": "Toyota Corolla Cross", "vehicle_type": "Crossover", "seat_count": 4, "sort_order": 14},
    {"brand": "Toyota", "model_name": "Raize", "display_name": "Toyota Raize", "vehicle_type": "Compact SUV", "seat_count": 4, "sort_order": 15},
    {"brand": "Toyota", "model_name": "Hilux Revo", "display_name": "Toyota Hilux Revo", "vehicle_type": "Pickup", "seat_count": 4, "sort_order": 16},
    {"brand": "Toyota", "model_name": "Coaster", "display_name": "Toyota Coaster", "vehicle_type": "Minibus", "seat_count": 23, "sort_order": 17},
    {"brand": "Toyota", "model_name": "Veloz", "display_name": "Toyota Veloz", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 18},
    {"brand": "Toyota", "model_name": "Tacoma", "display_name": "Toyota Tacoma", "vehicle_type": "Pickup", "seat_count": 4, "sort_order": 19},
    {"brand": "Lexus", "model_name": "NX300", "display_name": "Lexus NX300", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 20},
    {"brand": "Lexus", "model_name": "RX350", "display_name": "Lexus RX350", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 21},
    {"brand": "Lexus", "model_name": "LX570", "display_name": "Lexus LX570", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 22},
    {"brand": "Lexus", "model_name": "GX460", "display_name": "Lexus GX460", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 23},
    {"brand": "Hyundai", "model_name": "Staria", "display_name": "Hyundai Staria", "vehicle_type": "MPV / Minivan", "seat_count": 11, "sort_order": 24},
    {"brand": "Hyundai", "model_name": "Santa Fe", "display_name": "Hyundai Santa Fe", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 25},
    {"brand": "Hyundai", "model_name": "County", "display_name": "Hyundai County", "vehicle_type": "Bus", "seat_count": 25, "sort_order": 26},
    {"brand": "Hyundai", "model_name": "Solati", "display_name": "Hyundai Solati", "vehicle_type": "Minibus", "seat_count": 16, "sort_order": 27},
    {"brand": "Hyundai", "model_name": "Tucson", "display_name": "Hyundai Tucson", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 28},
    {"brand": "Kia", "model_name": "Carnival", "display_name": "Kia Carnival", "vehicle_type": "MPV / Minivan", "seat_count": 11, "sort_order": 29},
    {"brand": "Kia", "model_name": "Grand Carnival", "display_name": "Kia Grand Carnival", "vehicle_type": "MPV", "seat_count": 11, "sort_order": 30},
    {"brand": "Kia", "model_name": "Sorento", "display_name": "Kia Sorento", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 31},
    {"brand": "Kia", "model_name": "Morning", "display_name": "Kia Morning", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 32},
    {"brand": "Ford", "model_name": "Ranger Raptor", "display_name": "Ford Ranger Raptor", "vehicle_type": "Pickup", "seat_count": 4, "sort_order": 33},
    {"brand": "Ford", "model_name": "Transit", "display_name": "Ford Transit", "vehicle_type": "Van", "seat_count": 16, "sort_order": 34},
    {"brand": "Ford", "model_name": "Explorer", "display_name": "Ford Explorer", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 35},
    {"brand": "Ford", "model_name": "Territory", "display_name": "Ford Territory", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 36},
    {"brand": "Mitsubishi", "model_name": "Xpander", "display_name": "Mitsubishi Xpander", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 37},
    {"brand": "Mitsubishi", "model_name": "Pajero Sport", "display_name": "Mitsubishi Pajero Sport", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 38},
    {"brand": "Mitsubishi", "model_name": "Triton", "display_name": "Mitsubishi Triton", "vehicle_type": "Pickup", "seat_count": 4, "sort_order": 39},
    {"brand": "Honda", "model_name": "CR-V", "display_name": "Honda CR-V", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 40},
    {"brand": "Honda", "model_name": "HR-V", "display_name": "Honda HR-V", "vehicle_type": "Crossover", "seat_count": 4, "sort_order": 41},
    {"brand": "Honda", "model_name": "City", "display_name": "Honda City", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 42},
    {"brand": "Nissan", "model_name": "Navara", "display_name": "Nissan Navara", "vehicle_type": "Pickup", "seat_count": 4, "sort_order": 43},
    {"brand": "Nissan", "model_name": "Urvan", "display_name": "Nissan Urvan", "vehicle_type": "Van", "seat_count": 15, "sort_order": 44},
    {"brand": "Nissan", "model_name": "Terra", "display_name": "Nissan Terra", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 45},
    {"brand": "MG", "model_name": "ZS", "display_name": "MG ZS", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 46},
    {"brand": "BYD", "model_name": "Atto 3", "display_name": "BYD Atto 3", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 47},
    {"brand": "BYD", "model_name": "Dolphin", "display_name": "BYD Dolphin", "vehicle_type": "Electric Hatchback", "seat_count": 4, "sort_order": 48},
    {"brand": "Toyota", "model_name": "Vios", "display_name": "Toyota Vios", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 49},
    {"brand": "Toyota", "model_name": "Innova", "display_name": "Toyota Innova", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 50},
    {"brand": "Toyota", "model_name": "Avanza", "display_name": "Toyota Avanza", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 51},
    {"brand": "Toyota", "model_name": "Yaris Cross", "display_name": "Toyota Yaris Cross", "vehicle_type": "Crossover", "seat_count": 4, "sort_order": 52},
    {"brand": "Toyota", "model_name": "Vellfire", "display_name": "Toyota Vellfire", "vehicle_type": "Luxury MPV", "seat_count": 7, "sort_order": 53},
    {"brand": "Toyota", "model_name": "Crown", "display_name": "Toyota Crown", "vehicle_type": "Luxury Sedan", "seat_count": 4, "sort_order": 54},
    {"brand": "Toyota", "model_name": "Granvia", "display_name": "Toyota Granvia", "vehicle_type": "VIP Van", "seat_count": 9, "sort_order": 55},
    {"brand": "Toyota", "model_name": "4Runner", "display_name": "Toyota 4Runner", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 56},
    {"brand": "Toyota", "model_name": "bZ4X", "display_name": "Toyota bZ4X", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 57},
    {"brand": "Lexus", "model_name": "ES300h", "display_name": "Lexus ES300h", "vehicle_type": "Luxury Hybrid Sedan", "seat_count": 4, "sort_order": 58},
    {"brand": "Lexus", "model_name": "LM350h", "display_name": "Lexus LM350h", "vehicle_type": "Luxury MPV", "seat_count": 7, "sort_order": 59},
    {"brand": "Lexus", "model_name": "LX600", "display_name": "Lexus LX600", "vehicle_type": "Luxury SUV", "seat_count": 7, "sort_order": 60},
    {"brand": "Lexus", "model_name": "IS250", "display_name": "Lexus IS250", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 61},
    {"brand": "Lexus", "model_name": "RX450h", "display_name": "Lexus RX450h", "vehicle_type": "Hybrid SUV", "seat_count": 4, "sort_order": 62},
    {"brand": "Hyundai", "model_name": "Elantra", "display_name": "Hyundai Elantra", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 63},
    {"brand": "Hyundai", "model_name": "Accent", "display_name": "Hyundai Accent", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 64},
    {"brand": "Hyundai", "model_name": "Ioniq 5", "display_name": "Hyundai Ioniq 5", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 65},
    {"brand": "Hyundai", "model_name": "Kona", "display_name": "Hyundai Kona", "vehicle_type": "Compact SUV", "seat_count": 4, "sort_order": 66},
    {"brand": "Kia", "model_name": "Seltos", "display_name": "Kia Seltos", "vehicle_type": "Compact SUV", "seat_count": 4, "sort_order": 67},
    {"brand": "Kia", "model_name": "K5", "display_name": "Kia K5", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 68},
    {"brand": "Kia", "model_name": "EV6", "display_name": "Kia EV6", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 69},
    {"brand": "Kia", "model_name": "Soluto", "display_name": "Kia Soluto", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 70},
    {"brand": "Ford", "model_name": "Ranger", "display_name": "Ford Ranger", "vehicle_type": "Pickup", "seat_count": 4, "sort_order": 71},
    {"brand": "Ford", "model_name": "F-150", "display_name": "Ford F-150", "vehicle_type": "Pickup", "seat_count": 4, "sort_order": 72},
    {"brand": "Mazda", "model_name": "Mazda 3", "display_name": "Mazda 3", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 73},
    {"brand": "Mazda", "model_name": "CX-5", "display_name": "Mazda CX-5", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 74},
    {"brand": "Mazda", "model_name": "CX-8", "display_name": "Mazda CX-8", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 75},
    {"brand": "Mazda", "model_name": "CX-30", "display_name": "Mazda CX-30", "vehicle_type": "Crossover", "seat_count": 4, "sort_order": 76},
    {"brand": "Mazda", "model_name": "BT-50", "display_name": "Mazda BT-50", "vehicle_type": "Pickup", "seat_count": 4, "sort_order": 77},
    {"brand": "Nissan", "model_name": "Almera", "display_name": "Nissan Almera", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 78},
    {"brand": "Nissan", "model_name": "Kicks e-POWER", "display_name": "Nissan Kicks e-POWER", "vehicle_type": "Compact SUV", "seat_count": 4, "sort_order": 79},
    {"brand": "Nissan", "model_name": "Serena", "display_name": "Nissan Serena", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 80},
    {"brand": "Nissan", "model_name": "Patrol", "display_name": "Nissan Patrol", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 81},
    {"brand": "Mitsubishi", "model_name": "Xpander Cross", "display_name": "Mitsubishi Xpander Cross", "vehicle_type": "Crossover MPV", "seat_count": 7, "sort_order": 82},
    {"brand": "Mitsubishi", "model_name": "Outlander", "display_name": "Mitsubishi Outlander", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 83},
    {"brand": "Mitsubishi", "model_name": "Attrage", "display_name": "Mitsubishi Attrage", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 84},
    {"brand": "Honda", "model_name": "Accord", "display_name": "Honda Accord", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 85},
    {"brand": "Honda", "model_name": "BR-V", "display_name": "Honda BR-V", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 86},
    {"brand": "Honda", "model_name": "Odyssey", "display_name": "Honda Odyssey", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 87},
    {"brand": "Mercedes-Benz", "model_name": "E-Class", "display_name": "Mercedes-Benz E-Class", "vehicle_type": "Luxury Sedan", "seat_count": 4, "sort_order": 88},
    {"brand": "Mercedes-Benz", "model_name": "S-Class", "display_name": "Mercedes-Benz S-Class", "vehicle_type": "Luxury Sedan", "seat_count": 4, "sort_order": 89},
    {"brand": "Mercedes-Benz", "model_name": "GLC", "display_name": "Mercedes-Benz GLC", "vehicle_type": "Luxury SUV", "seat_count": 4, "sort_order": 90},
    {"brand": "Mercedes-Benz", "model_name": "GLE", "display_name": "Mercedes-Benz GLE", "vehicle_type": "Luxury SUV", "seat_count": 7, "sort_order": 91},
    {"brand": "Mercedes-Benz", "model_name": "V-Class", "display_name": "Mercedes-Benz V-Class", "vehicle_type": "VIP Van", "seat_count": 7, "sort_order": 92},
    {"brand": "Mercedes-Benz", "model_name": "Sprinter", "display_name": "Mercedes-Benz Sprinter", "vehicle_type": "Minibus", "seat_count": 16, "sort_order": 93},
    {"brand": "Mercedes-Benz", "model_name": "G-Class", "display_name": "Mercedes-Benz G-Class", "vehicle_type": "Luxury SUV", "seat_count": 4, "sort_order": 94},
    {"brand": "BMW", "model_name": "5 Series", "display_name": "BMW 5 Series", "vehicle_type": "Luxury Sedan", "seat_count": 4, "sort_order": 95},
    {"brand": "BMW", "model_name": "7 Series", "display_name": "BMW 7 Series", "vehicle_type": "Luxury Sedan", "seat_count": 4, "sort_order": 96},
    {"brand": "BMW", "model_name": "X5", "display_name": "BMW X5", "vehicle_type": "Luxury SUV", "seat_count": 7, "sort_order": 97},
    {"brand": "BMW", "model_name": "X7", "display_name": "BMW X7", "vehicle_type": "Luxury SUV", "seat_count": 7, "sort_order": 98},
    {"brand": "BYD", "model_name": "Seal", "display_name": "BYD Seal", "vehicle_type": "Electric Sedan", "seat_count": 4, "sort_order": 99},
    {"brand": "BYD", "model_name": "Han", "display_name": "BYD Han", "vehicle_type": "Electric Sedan", "seat_count": 4, "sort_order": 100},
    {"brand": "Tank", "model_name": "Tank 300", "display_name": "Tank 300", "vehicle_type": "Off-road SUV", "seat_count": 4, "sort_order": 101},
    {"brand": "Geely", "model_name": "Coolray", "display_name": "Geely Coolray", "vehicle_type": "Crossover", "seat_count": 4, "sort_order": 102},
    {"brand": "Geely", "model_name": "Monjaro", "display_name": "Geely Monjaro", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 103},
    {"brand": "Toyota", "model_name": "Corolla", "display_name": "Toyota Corolla", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 104},
    {"brand": "Toyota", "model_name": "Prius Plus", "display_name": "Toyota Prius Plus", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 105},
    {"brand": "Toyota", "model_name": "Yaris", "display_name": "Toyota Yaris", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 106},
    {"brand": "Toyota", "model_name": "Urban Cruiser", "display_name": "Toyota Urban Cruiser", "vehicle_type": "Compact SUV", "seat_count": 4, "sort_order": 107},
    {"brand": "Toyota", "model_name": "RAV4", "display_name": "Toyota RAV4", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 108},
    {"brand": "Toyota", "model_name": "RAV4 Hybrid", "display_name": "Toyota RAV4 Hybrid", "vehicle_type": "Hybrid SUV", "seat_count": 4, "sort_order": 109},
    {"brand": "Toyota", "model_name": "LiteAce", "display_name": "Toyota LiteAce", "vehicle_type": "Van", "seat_count": 7, "sort_order": 110},
    {"brand": "Toyota", "model_name": "TownAce", "display_name": "Toyota TownAce", "vehicle_type": "Van", "seat_count": 7, "sort_order": 111},
    {"brand": "Toyota", "model_name": "Sienta", "display_name": "Toyota Sienta", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 112},
    {"brand": "Toyota", "model_name": "Noah", "display_name": "Toyota Noah", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 113},
    {"brand": "Toyota", "model_name": "Voxy", "display_name": "Toyota Voxy", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 114},
    {"brand": "Toyota", "model_name": "Esquire", "display_name": "Toyota Esquire", "vehicle_type": "Luxury MPV", "seat_count": 7, "sort_order": 115},
    {"brand": "Toyota", "model_name": "Century", "display_name": "Toyota Century", "vehicle_type": "Luxury SUV", "seat_count": 4, "sort_order": 116},
    {"brand": "Lexus", "model_name": "RX500h", "display_name": "Lexus RX500h", "vehicle_type": "Luxury Hybrid SUV", "seat_count": 4, "sort_order": 117},
    {"brand": "Lexus", "model_name": "TX", "display_name": "Lexus TX", "vehicle_type": "Luxury 3-Row SUV", "seat_count": 7, "sort_order": 118},
    {"brand": "Lexus", "model_name": "RZ450e", "display_name": "Lexus RZ450e", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 119},
    {"brand": "Honda", "model_name": "Civic", "display_name": "Honda Civic", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 120},
    {"brand": "Honda", "model_name": "Fit", "display_name": "Honda Fit / Jazz", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 121},
    {"brand": "Honda", "model_name": "Pilot", "display_name": "Honda Pilot", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 122},
    {"brand": "Honda", "model_name": "WR-V", "display_name": "Honda WR-V", "vehicle_type": "Compact SUV", "seat_count": 4, "sort_order": 123},
    {"brand": "Honda", "model_name": "Freed", "display_name": "Honda Freed", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 124},
    {"brand": "Honda", "model_name": "StepWGN", "display_name": "Honda StepWGN", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 125},
    {"brand": "Nissan", "model_name": "Sunny", "display_name": "Nissan Sunny / Versa", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 126},
    {"brand": "Nissan", "model_name": "Sentra", "display_name": "Nissan Sentra", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 127},
    {"brand": "Nissan", "model_name": "Altima", "display_name": "Nissan Altima", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 128},
    {"brand": "Nissan", "model_name": "NV200", "display_name": "Nissan NV200 Taxi", "vehicle_type": "Taxi Van", "seat_count": 5, "sort_order": 129},
    {"brand": "Nissan", "model_name": "Qashqai", "display_name": "Nissan Qashqai", "vehicle_type": "Crossover", "seat_count": 4, "sort_order": 130},
    {"brand": "Nissan", "model_name": "X-Trail", "display_name": "Nissan X-Trail / Rogue", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 131},
    {"brand": "Nissan", "model_name": "Leaf", "display_name": "Nissan Leaf", "vehicle_type": "Electric Hatchback", "seat_count": 4, "sort_order": 132},
    {"brand": "Hyundai", "model_name": "Sonata", "display_name": "Hyundai Sonata", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 133},
    {"brand": "Hyundai", "model_name": "Grand i10", "display_name": "Hyundai Grand i10", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 134},
    {"brand": "Hyundai", "model_name": "i20", "display_name": "Hyundai i20", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 135},
    {"brand": "Hyundai", "model_name": "i30", "display_name": "Hyundai i30", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 136},
    {"brand": "Hyundai", "model_name": "Venue", "display_name": "Hyundai Venue", "vehicle_type": "Compact SUV", "seat_count": 4, "sort_order": 137},
    {"brand": "Hyundai", "model_name": "Alcazar", "display_name": "Hyundai Alcazar", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 138},
    {"brand": "Hyundai", "model_name": "Palisade", "display_name": "Hyundai Palisade", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 139},
    {"brand": "Hyundai", "model_name": "Ioniq 6", "display_name": "Hyundai Ioniq 6", "vehicle_type": "Electric Sedan", "seat_count": 4, "sort_order": 140},
    {"brand": "Kia", "model_name": "Picanto", "display_name": "Kia Picanto", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 141},
    {"brand": "Kia", "model_name": "Rio", "display_name": "Kia Rio", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 142},
    {"brand": "Kia", "model_name": "Ceed", "display_name": "Kia Ceed", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 143},
    {"brand": "Kia", "model_name": "Carens", "display_name": "Kia Carens", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 144},
    {"brand": "Kia", "model_name": "Sportage", "display_name": "Kia Sportage", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 145},
    {"brand": "Kia", "model_name": "Telluride", "display_name": "Kia Telluride", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 146},
    {"brand": "Kia", "model_name": "EV9", "display_name": "Kia EV9", "vehicle_type": "Electric 3-Row SUV", "seat_count": 7, "sort_order": 147},
    {"brand": "Tesla", "model_name": "Model 3", "display_name": "Tesla Model 3", "vehicle_type": "Electric Sedan", "seat_count": 4, "sort_order": 148},
    {"brand": "Tesla", "model_name": "Model Y", "display_name": "Tesla Model Y", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 149},
    {"brand": "Tesla", "model_name": "Model S", "display_name": "Tesla Model S", "vehicle_type": "Electric Luxury Sedan", "seat_count": 4, "sort_order": 150},
    {"brand": "Tesla", "model_name": "Model X", "display_name": "Tesla Model X", "vehicle_type": "Electric Luxury SUV", "seat_count": 7, "sort_order": 151},
    {"brand": "Volkswagen", "model_name": "Jetta", "display_name": "Volkswagen Jetta", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 152},
    {"brand": "Volkswagen", "model_name": "Passat", "display_name": "Volkswagen Passat", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 153},
    {"brand": "Volkswagen", "model_name": "Golf", "display_name": "Volkswagen Golf", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 154},
    {"brand": "Volkswagen", "model_name": "Touran", "display_name": "Volkswagen Touran", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 155},
    {"brand": "Volkswagen", "model_name": "Tiguan", "display_name": "Volkswagen Tiguan", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 156},
    {"brand": "Volkswagen", "model_name": "ID.4", "display_name": "Volkswagen ID.4", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 157},
    {"brand": "Volkswagen", "model_name": "Caravelle", "display_name": "Volkswagen Caravelle", "vehicle_type": "VIP Van", "seat_count": 9, "sort_order": 158},
    {"brand": "Skoda", "model_name": "Octavia", "display_name": "Skoda Octavia", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 159},
    {"brand": "Skoda", "model_name": "Superb", "display_name": "Skoda Superb", "vehicle_type": "Luxury Sedan", "seat_count": 4, "sort_order": 160},
    {"brand": "Skoda", "model_name": "Kodiaq", "display_name": "Skoda Kodiaq", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 161},
    {"brand": "Skoda", "model_name": "Fabia", "display_name": "Skoda Fabia", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 162},
    {"brand": "BYD", "model_name": "Song Plus", "display_name": "BYD Song Plus", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 163},
    {"brand": "BYD", "model_name": "Tang", "display_name": "BYD Tang", "vehicle_type": "Electric 7-Seat SUV", "seat_count": 7, "sort_order": 164},
    {"brand": "BYD", "model_name": "Yuan Plus", "display_name": "BYD Yuan Plus", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 165},
    {"brand": "BYD", "model_name": "Qin Plus", "display_name": "BYD Qin Plus", "vehicle_type": "Electric Sedan", "seat_count": 4, "sort_order": 166},
    {"brand": "BYD", "model_name": "Seagull", "display_name": "BYD Seagull", "vehicle_type": "Compact EV", "seat_count": 4, "sort_order": 167},
    {"brand": "BYD", "model_name": "e6", "display_name": "BYD e6 Taxi", "vehicle_type": "Electric Taxi MPV", "seat_count": 5, "sort_order": 168},
    {"brand": "Geely", "model_name": "Emgrand", "display_name": "Geely Emgrand", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 169},
    {"brand": "Geely", "model_name": "Azkarra", "display_name": "Geely Azkarra", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 170},
    {"brand": "Geely", "model_name": "Okavango", "display_name": "Geely Okavango", "vehicle_type": "7-Seat SUV", "seat_count": 7, "sort_order": 171},
    {"brand": "Geely", "model_name": "Geometry C", "display_name": "Geely Geometry C", "vehicle_type": "Electric Crossover", "seat_count": 4, "sort_order": 172},
    {"brand": "Suzuki", "model_name": "Swift", "display_name": "Suzuki Swift", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 173},
    {"brand": "Suzuki", "model_name": "Ertiga", "display_name": "Suzuki Ertiga", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 174},
    {"brand": "Suzuki", "model_name": "XL7", "display_name": "Suzuki XL7", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 175},
    {"brand": "Suzuki", "model_name": "Ciaz", "display_name": "Suzuki Ciaz", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 176},
    {"brand": "Suzuki", "model_name": "APV", "display_name": "Suzuki APV", "vehicle_type": "Van", "seat_count": 8, "sort_order": 177},
    {"brand": "Peugeot", "model_name": "301", "display_name": "Peugeot 301", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 178},
    {"brand": "Peugeot", "model_name": "508", "display_name": "Peugeot 508", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 179},
    {"brand": "Peugeot", "model_name": "3008", "display_name": "Peugeot 3008", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 180},
    {"brand": "Peugeot", "model_name": "5008", "display_name": "Peugeot 5008", "vehicle_type": "7-Seat SUV", "seat_count": 7, "sort_order": 181},
    {"brand": "Renault", "model_name": "Logan", "display_name": "Renault Logan", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 182},
    {"brand": "Renault", "model_name": "Megane", "display_name": "Renault Megane", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 183},
    {"brand": "Renault", "model_name": "Duster", "display_name": "Renault Duster", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 184},
    {"brand": "Chevrolet", "model_name": "Cruze", "display_name": "Chevrolet Cruze", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 185},
    {"brand": "Chevrolet", "model_name": "Malibu", "display_name": "Chevrolet Malibu", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 186},
    {"brand": "Chevrolet", "model_name": "Suburban", "display_name": "Chevrolet Suburban", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 187},
    {"brand": "Chevrolet", "model_name": "Colorado", "display_name": "Chevrolet Colorado", "vehicle_type": "Pickup", "seat_count": 4, "sort_order": 188},
    {"brand": "Wuling", "model_name": "Hongguang S", "display_name": "Wuling Hongguang S", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 189},
    {"brand": "Wuling", "model_name": "Sunshine", "display_name": "Wuling Sunshine", "vehicle_type": "Van", "seat_count": 8, "sort_order": 190},
    {"brand": "Wuling", "model_name": "Cortez", "display_name": "Wuling Cortez", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 191},
    {"brand": "MG", "model_name": "MG 5", "display_name": "MG 5", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 192},
    {"brand": "MG", "model_name": "HS", "display_name": "MG HS", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 193},
    {"brand": "MG", "model_name": "Maxus 9", "display_name": "MG Maxus 9", "vehicle_type": "Electric VIP MPV", "seat_count": 7, "sort_order": 194},
    {"brand": "Mercedes-Benz", "model_name": "C-Class", "display_name": "Mercedes-Benz C-Class", "vehicle_type": "Luxury Sedan", "seat_count": 4, "sort_order": 195},
    {"brand": "BMW", "model_name": "3 Series", "display_name": "BMW 3 Series", "vehicle_type": "Luxury Sedan", "seat_count": 4, "sort_order": 196},
    {"brand": "Audi", "model_name": "A4", "display_name": "Audi A4", "vehicle_type": "Luxury Sedan", "seat_count": 4, "sort_order": 197},
    {"brand": "Audi", "model_name": "A6", "display_name": "Audi A6", "vehicle_type": "Luxury Sedan", "seat_count": 4, "sort_order": 198},
    {"brand": "Volvo", "model_name": "XC90", "display_name": "Volvo XC90", "vehicle_type": "Luxury SUV", "seat_count": 7, "sort_order": 199},
    {"brand": "LEVC", "model_name": "TX", "display_name": "LEVC TX Electric London Taxi", "vehicle_type": "Iconic Taxi", "seat_count": 6, "sort_order": 200},
]


def ensure_default_vehicle_models(db: Session) -> None:
    try:
        existing_models = set(
            db.execute(select(VehicleModel.brand, VehicleModel.model_name)).all()
        )
        import uuid
        added = False
        for item in DEFAULT_CAR_MODELS:
            key = (item["brand"], item["model_name"])
            if key not in existing_models:
                v_model = VehicleModel(
                    id=uuid.uuid4(),
                    brand=item["brand"],
                    model_name=item["model_name"],
                    display_name=item["display_name"],
                    vehicle_type=item["vehicle_type"],
                    seat_count=item["seat_count"],
                    is_active=True,
                    sort_order=item["sort_order"],
                )
                db.add(v_model)
                added = True
        if added:
            db.commit()
    except Exception:
        db.rollback()