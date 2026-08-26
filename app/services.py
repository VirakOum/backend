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
    # --- 1. TOYOTA (Top Taxis & Transports in Cambodia / Global) ---
    {"brand": "Toyota", "model_name": "Prius", "display_name": "Toyota Prius", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 1},
    {"brand": "Toyota", "model_name": "Alphard", "display_name": "Toyota Alphard", "vehicle_type": "MPV / Minivan", "seat_count": 7, "sort_order": 2},
    {"brand": "Toyota", "model_name": "Vios", "display_name": "Toyota Vios", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 3},
    {"brand": "Toyota", "model_name": "Camry", "display_name": "Toyota Camry", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 4},
    {"brand": "Toyota", "model_name": "HiAce", "display_name": "Toyota HiAce", "vehicle_type": "Van", "seat_count": 15, "sort_order": 5},
    {"brand": "Toyota", "model_name": "Innova", "display_name": "Toyota Innova", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 6},
    {"brand": "Toyota", "model_name": "Sienna", "display_name": "Toyota Sienna", "vehicle_type": "Minivan", "seat_count": 7, "sort_order": 7},
    {"brand": "Toyota", "model_name": "Fortuner", "display_name": "Toyota Fortuner", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 8},
    {"brand": "Toyota", "model_name": "Highlander", "display_name": "Toyota Highlander", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 9},
    {"brand": "Toyota", "model_name": "Corolla", "display_name": "Toyota Corolla", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 10},
    {"brand": "Toyota", "model_name": "Corolla Cross", "display_name": "Toyota Corolla Cross", "vehicle_type": "Crossover", "seat_count": 4, "sort_order": 11},
    {"brand": "Toyota", "model_name": "Raize", "display_name": "Toyota Raize", "vehicle_type": "Compact SUV", "seat_count": 4, "sort_order": 12},
    {"brand": "Toyota", "model_name": "Veloz", "display_name": "Toyota Veloz", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 13},
    {"brand": "Toyota", "model_name": "Avanza", "display_name": "Toyota Avanza", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 14},
    {"brand": "Toyota", "model_name": "Vellfire", "display_name": "Toyota Vellfire", "vehicle_type": "Luxury MPV", "seat_count": 7, "sort_order": 15},
    {"brand": "Toyota", "model_name": "Land Cruiser", "display_name": "Toyota Land Cruiser", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 16},
    {"brand": "Toyota", "model_name": "Land Cruiser Prado", "display_name": "Toyota Land Cruiser Prado", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 17},
    {"brand": "Toyota", "model_name": "Hilux Revo", "display_name": "Toyota Hilux Revo", "vehicle_type": "Pickup", "seat_count": 4, "sort_order": 18},
    {"brand": "Toyota", "model_name": "Coaster", "display_name": "Toyota Coaster", "vehicle_type": "Minibus", "seat_count": 23, "sort_order": 19},
    {"brand": "Toyota", "model_name": "Granvia", "display_name": "Toyota Granvia", "vehicle_type": "VIP Van", "seat_count": 9, "sort_order": 20},
    {"brand": "Toyota", "model_name": "Crown", "display_name": "Toyota Crown", "vehicle_type": "Luxury Sedan", "seat_count": 4, "sort_order": 21},
    {"brand": "Toyota", "model_name": "RAV4", "display_name": "Toyota RAV4", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 22},
    {"brand": "Toyota", "model_name": "RAV4 Hybrid", "display_name": "Toyota RAV4 Hybrid", "vehicle_type": "Hybrid SUV", "seat_count": 4, "sort_order": 23},
    {"brand": "Toyota", "model_name": "Yaris Cross", "display_name": "Toyota Yaris Cross", "vehicle_type": "Crossover", "seat_count": 4, "sort_order": 24},
    {"brand": "Toyota", "model_name": "Yaris", "display_name": "Toyota Yaris", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 25},
    {"brand": "Toyota", "model_name": "Prius Plus", "display_name": "Toyota Prius Plus", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 26},
    {"brand": "Toyota", "model_name": "Innova Zenix", "display_name": "Toyota Innova Zenix", "vehicle_type": "Hybrid MPV", "seat_count": 7, "sort_order": 27},
    {"brand": "Toyota", "model_name": "Innova Crysta", "display_name": "Toyota Innova Crysta", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 28},
    {"brand": "Toyota", "model_name": "Sienta", "display_name": "Toyota Sienta", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 29},
    {"brand": "Toyota", "model_name": "Noah", "display_name": "Toyota Noah", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 30},
    {"brand": "Toyota", "model_name": "Voxy", "display_name": "Toyota Voxy", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 31},
    {"brand": "Toyota", "model_name": "Esquire", "display_name": "Toyota Esquire", "vehicle_type": "Luxury MPV", "seat_count": 7, "sort_order": 32},
    {"brand": "Toyota", "model_name": "LiteAce", "display_name": "Toyota LiteAce", "vehicle_type": "Van", "seat_count": 7, "sort_order": 33},
    {"brand": "Toyota", "model_name": "TownAce", "display_name": "Toyota TownAce", "vehicle_type": "Van", "seat_count": 7, "sort_order": 34},
    {"brand": "Toyota", "model_name": "HiAce Commuter", "display_name": "Toyota HiAce Commuter", "vehicle_type": "Van", "seat_count": 16, "sort_order": 35},
    {"brand": "Toyota", "model_name": "HiAce Super Custom", "display_name": "Toyota HiAce Super Custom", "vehicle_type": "VIP Van", "seat_count": 10, "sort_order": 36},
    {"brand": "Toyota", "model_name": "GranAce", "display_name": "Toyota GranAce", "vehicle_type": "VIP Luxury Van", "seat_count": 8, "sort_order": 37},
    {"brand": "Toyota", "model_name": "Majesty", "display_name": "Toyota Majesty", "vehicle_type": "VIP Van", "seat_count": 11, "sort_order": 38},
    {"brand": "Toyota", "model_name": "Wigo", "display_name": "Toyota Wigo", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 39},
    {"brand": "Toyota", "model_name": "Agya", "display_name": "Toyota Agya", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 40},
    {"brand": "Toyota", "model_name": "Calya", "display_name": "Toyota Calya", "vehicle_type": "Compact MPV", "seat_count": 7, "sort_order": 41},
    {"brand": "Toyota", "model_name": "Rush", "display_name": "Toyota Rush", "vehicle_type": "7-Seat SUV", "seat_count": 7, "sort_order": 42},
    {"brand": "Toyota", "model_name": "Rumion", "display_name": "Toyota Rumion", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 43},
    {"brand": "Toyota", "model_name": "Urban Cruiser", "display_name": "Toyota Urban Cruiser", "vehicle_type": "Compact SUV", "seat_count": 4, "sort_order": 44},
    {"brand": "Toyota", "model_name": "Crown Signia", "display_name": "Toyota Crown Signia", "vehicle_type": "Luxury Hybrid SUV", "seat_count": 4, "sort_order": 45},
    {"brand": "Toyota", "model_name": "Crown Crossover", "display_name": "Toyota Crown Crossover", "vehicle_type": "Luxury Hybrid Sedan", "seat_count": 4, "sort_order": 46},
    {"brand": "Toyota", "model_name": "Grand Highlander", "display_name": "Toyota Grand Highlander", "vehicle_type": "3-Row SUV", "seat_count": 8, "sort_order": 47},
    {"brand": "Toyota", "model_name": "Sequoia", "display_name": "Toyota Sequoia", "vehicle_type": "Luxury SUV", "seat_count": 8, "sort_order": 48},
    {"brand": "Toyota", "model_name": "4Runner", "display_name": "Toyota 4Runner", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 49},
    {"brand": "Toyota", "model_name": "bZ4X", "display_name": "Toyota bZ4X", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 50},
    {"brand": "Toyota", "model_name": "bZ3", "display_name": "Toyota bZ3 EV Taxi", "vehicle_type": "Electric Sedan", "seat_count": 4, "sort_order": 51},
    {"brand": "Toyota", "model_name": "Proace Verso", "display_name": "Toyota Proace Verso", "vehicle_type": "Passenger Van", "seat_count": 9, "sort_order": 52},
    {"brand": "Toyota", "model_name": "Proace City", "display_name": "Toyota Proace City", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 53},
    {"brand": "Toyota", "model_name": "Tacoma", "display_name": "Toyota Tacoma", "vehicle_type": "Pickup", "seat_count": 4, "sort_order": 54},
    {"brand": "Toyota", "model_name": "Century", "display_name": "Toyota Century", "vehicle_type": "Luxury SUV", "seat_count": 4, "sort_order": 55},

    # --- 2. BYD (Extensive EV & Hybrid Taxi / Passenger Range) ---
    {"brand": "BYD", "model_name": "e6", "display_name": "BYD e6 Taxi", "vehicle_type": "Electric Taxi MPV", "seat_count": 5, "sort_order": 56},
    {"brand": "BYD", "model_name": "D1", "display_name": "BYD D1 Ride-Hailing EV", "vehicle_type": "Purpose-Built Taxi MPV", "seat_count": 5, "sort_order": 57},
    {"brand": "BYD", "model_name": "Qin Plus EV", "display_name": "BYD Qin Plus EV", "vehicle_type": "Electric Sedan Taxi", "seat_count": 4, "sort_order": 58},
    {"brand": "BYD", "model_name": "Qin Plus DM-i", "display_name": "BYD Qin Plus DM-i", "vehicle_type": "Hybrid Sedan Taxi", "seat_count": 4, "sort_order": 59},
    {"brand": "BYD", "model_name": "Qin Pro", "display_name": "BYD Qin Pro EV", "vehicle_type": "Electric Sedan", "seat_count": 4, "sort_order": 60},
    {"brand": "BYD", "model_name": "Qin L DM-i", "display_name": "BYD Qin L DM-i", "vehicle_type": "Super Hybrid Sedan", "seat_count": 4, "sort_order": 61},
    {"brand": "BYD", "model_name": "Seal", "display_name": "BYD Seal EV", "vehicle_type": "Electric Sedan", "seat_count": 4, "sort_order": 62},
    {"brand": "BYD", "model_name": "Seal 06 DM-i", "display_name": "BYD Seal 06 DM-i", "vehicle_type": "Super Hybrid Sedan", "seat_count": 4, "sort_order": 63},
    {"brand": "BYD", "model_name": "Seal U", "display_name": "BYD Seal U EV", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 64},
    {"brand": "BYD", "model_name": "Dolphin", "display_name": "BYD Dolphin", "vehicle_type": "Electric Hatchback", "seat_count": 4, "sort_order": 65},
    {"brand": "BYD", "model_name": "Seagull", "display_name": "BYD Seagull / Dolphin Mini", "vehicle_type": "Compact EV Taxi", "seat_count": 4, "sort_order": 66},
    {"brand": "BYD", "model_name": "Atto 3", "display_name": "BYD Atto 3", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 67},
    {"brand": "BYD", "model_name": "Yuan Plus", "display_name": "BYD Yuan Plus", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 68},
    {"brand": "BYD", "model_name": "Yuan Pro", "display_name": "BYD Yuan Pro", "vehicle_type": "Compact Electric SUV", "seat_count": 4, "sort_order": 69},
    {"brand": "BYD", "model_name": "Yuan UP", "display_name": "BYD Yuan UP", "vehicle_type": "Urban Electric SUV", "seat_count": 4, "sort_order": 70},
    {"brand": "BYD", "model_name": "Han", "display_name": "BYD Han EV", "vehicle_type": "Electric Luxury Sedan", "seat_count": 4, "sort_order": 71},
    {"brand": "BYD", "model_name": "Han DM-i", "display_name": "BYD Han DM-i", "vehicle_type": "Executive Hybrid Sedan", "seat_count": 4, "sort_order": 72},
    {"brand": "BYD", "model_name": "Tang", "display_name": "BYD Tang EV", "vehicle_type": "Electric 7-Seat SUV", "seat_count": 7, "sort_order": 73},
    {"brand": "BYD", "model_name": "Tang DM-i", "display_name": "BYD Tang DM-i", "vehicle_type": "7-Seat Hybrid SUV", "seat_count": 7, "sort_order": 74},
    {"brand": "BYD", "model_name": "Song Plus", "display_name": "BYD Song Plus EV", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 75},
    {"brand": "BYD", "model_name": "Song Plus DM-i", "display_name": "BYD Song Plus DM-i", "vehicle_type": "Plug-in Hybrid SUV", "seat_count": 4, "sort_order": 76},
    {"brand": "BYD", "model_name": "Song Pro DM-i", "display_name": "BYD Song Pro DM-i", "vehicle_type": "Hybrid SUV", "seat_count": 4, "sort_order": 77},
    {"brand": "BYD", "model_name": "Song Max", "display_name": "BYD Song Max", "vehicle_type": "7-Seat MPV Taxi", "seat_count": 7, "sort_order": 78},
    {"brand": "BYD", "model_name": "Song Max DM-i", "display_name": "BYD Song Max DM-i", "vehicle_type": "7-Seat Hybrid MPV", "seat_count": 7, "sort_order": 79},
    {"brand": "BYD", "model_name": "Song L EV", "display_name": "BYD Song L EV", "vehicle_type": "Electric Coupe SUV", "seat_count": 4, "sort_order": 80},
    {"brand": "BYD", "model_name": "Song L DM-i", "display_name": "BYD Song L DM-i", "vehicle_type": "Super Hybrid SUV", "seat_count": 4, "sort_order": 81},
    {"brand": "BYD", "model_name": "Destroyer 05", "display_name": "BYD Destroyer 05", "vehicle_type": "Hybrid Sedan Taxi", "seat_count": 4, "sort_order": 82},
    {"brand": "BYD", "model_name": "Chazor", "display_name": "BYD Chazor DM-i", "vehicle_type": "Plug-in Sedan Taxi", "seat_count": 4, "sort_order": 83},
    {"brand": "BYD", "model_name": "M6", "display_name": "BYD M6 Electric MPV", "vehicle_type": "Electric 7-Seat MPV Taxi", "seat_count": 7, "sort_order": 84},
    {"brand": "BYD", "model_name": "e2", "display_name": "BYD e2 EV", "vehicle_type": "Electric Hatchback Taxi", "seat_count": 4, "sort_order": 85},
    {"brand": "BYD", "model_name": "e3", "display_name": "BYD e3 EV", "vehicle_type": "Electric Sedan Taxi", "seat_count": 4, "sort_order": 86},
    {"brand": "BYD", "model_name": "e5", "display_name": "BYD e5 EV", "vehicle_type": "Electric Fleet Taxi", "seat_count": 4, "sort_order": 87},
    {"brand": "BYD", "model_name": "e9", "display_name": "BYD e9 EV", "vehicle_type": "Executive Electric Sedan", "seat_count": 4, "sort_order": 88},
    {"brand": "BYD", "model_name": "F3", "display_name": "BYD F3", "vehicle_type": "Compact Sedan", "seat_count": 4, "sort_order": 89},
    {"brand": "BYD", "model_name": "F3DM", "display_name": "BYD F3DM Hybrid", "vehicle_type": "Hybrid Sedan", "seat_count": 4, "sort_order": 90},
    {"brand": "BYD", "model_name": "G3", "display_name": "BYD G3", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 91},
    {"brand": "BYD", "model_name": "G5", "display_name": "BYD G5", "vehicle_type": "Turbo Sedan", "seat_count": 4, "sort_order": 92},
    {"brand": "BYD", "model_name": "G6", "display_name": "BYD G6", "vehicle_type": "Mid-size Sedan", "seat_count": 4, "sort_order": 93},
    {"brand": "BYD", "model_name": "Surui", "display_name": "BYD Surui", "vehicle_type": "Compact Sedan", "seat_count": 4, "sort_order": 94},
    {"brand": "BYD", "model_name": "Sirui", "display_name": "BYD Sirui", "vehicle_type": "Luxury Sedan", "seat_count": 4, "sort_order": 95},
    {"brand": "BYD", "model_name": "Sealion 6", "display_name": "BYD Sealion 6 DM-i", "vehicle_type": "Super Hybrid SUV", "seat_count": 4, "sort_order": 96},
    {"brand": "BYD", "model_name": "Sealion 7", "display_name": "BYD Sealion 7 EV", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 97},
    {"brand": "BYD", "model_name": "Sealion 05 DM-i", "display_name": "BYD Sealion 05 DM-i", "vehicle_type": "Hybrid SUV", "seat_count": 4, "sort_order": 98},
    {"brand": "BYD", "model_name": "Corvette 07", "display_name": "BYD Corvette 07 / Frigate 07", "vehicle_type": "PHEV Mid-size SUV", "seat_count": 4, "sort_order": 99},
    {"brand": "BYD", "model_name": "Denza D9", "display_name": "BYD Denza D9 VIP MPV", "vehicle_type": "Luxury VIP Electric MPV", "seat_count": 7, "sort_order": 100},
    {"brand": "BYD", "model_name": "Denza D9 DM-i", "display_name": "BYD Denza D9 DM-i", "vehicle_type": "Luxury VIP Hybrid MPV", "seat_count": 7, "sort_order": 101},
    {"brand": "BYD", "model_name": "Denza N7", "display_name": "BYD Denza N7", "vehicle_type": "Luxury Electric SUV", "seat_count": 4, "sort_order": 102},
    {"brand": "BYD", "model_name": "Denza N8", "display_name": "BYD Denza N8", "vehicle_type": "Luxury 7-Seat SUV", "seat_count": 7, "sort_order": 103},
    {"brand": "BYD", "model_name": "Denza Z9 GT", "display_name": "BYD Denza Z9 GT", "vehicle_type": "Luxury Executive Tourer", "seat_count": 4, "sort_order": 104},
    {"brand": "BYD", "model_name": "Xia", "display_name": "BYD Xia Flagship MPV", "vehicle_type": "Luxury 7-Seat MPV", "seat_count": 7, "sort_order": 105},
    {"brand": "BYD", "model_name": "Yangwang U8", "display_name": "BYD Yangwang U8", "vehicle_type": "Ultra-Luxury Off-road SUV", "seat_count": 4, "sort_order": 106},
    {"brand": "BYD", "model_name": "Yangwang U7", "display_name": "BYD Yangwang U7", "vehicle_type": "Ultra-Luxury Electric Sedan", "seat_count": 4, "sort_order": 107},
    {"brand": "BYD", "model_name": "Shark", "display_name": "BYD Shark PHEV", "vehicle_type": "Hybrid Pickup", "seat_count": 4, "sort_order": 108},
    {"brand": "BYD", "model_name": "T3", "display_name": "BYD T3 Electric Van", "vehicle_type": "Electric Passenger Van", "seat_count": 5, "sort_order": 109},
    {"brand": "BYD", "model_name": "V9", "display_name": "BYD V9 Passenger Van", "vehicle_type": "Electric VIP Van", "seat_count": 9, "sort_order": 110},
    {"brand": "BYD", "model_name": "C6", "display_name": "BYD C6 Electric Coach", "vehicle_type": "Electric Minibus", "seat_count": 24, "sort_order": 111},
    {"brand": "BYD", "model_name": "K7", "display_name": "BYD K7 Electric Bus", "vehicle_type": "Electric Bus", "seat_count": 22, "sort_order": 112},
    {"brand": "BYD", "model_name": "K8", "display_name": "BYD K8 Electric Bus", "vehicle_type": "Electric Bus", "seat_count": 30, "sort_order": 113},
    {"brand": "BYD", "model_name": "K9", "display_name": "BYD K9 Electric City Bus", "vehicle_type": "Electric Bus", "seat_count": 36, "sort_order": 114},

    # --- 3. HYUNDAI (Popular Taxis, Starex, Staria, Buses in Cambodia) ---
    {"brand": "Hyundai", "model_name": "Starex", "display_name": "Hyundai Starex", "vehicle_type": "Minivan", "seat_count": 12, "sort_order": 115},
    {"brand": "Hyundai", "model_name": "Staria", "display_name": "Hyundai Staria", "vehicle_type": "MPV / Minivan", "seat_count": 11, "sort_order": 116},
    {"brand": "Hyundai", "model_name": "H1", "display_name": "Hyundai H1", "vehicle_type": "Van", "seat_count": 12, "sort_order": 117},
    {"brand": "Hyundai", "model_name": "Solati", "display_name": "Hyundai Solati", "vehicle_type": "Minibus", "seat_count": 16, "sort_order": 118},
    {"brand": "Hyundai", "model_name": "County", "display_name": "Hyundai County", "vehicle_type": "Bus", "seat_count": 25, "sort_order": 119},
    {"brand": "Hyundai", "model_name": "Universe", "display_name": "Hyundai Universe", "vehicle_type": "Bus", "seat_count": 45, "sort_order": 120},
    {"brand": "Hyundai", "model_name": "Universe Sleeper", "display_name": "Hyundai Universe Sleeper", "vehicle_type": "Sleeping Bus", "seat_count": 23, "sort_order": 121},
    {"brand": "Hyundai", "model_name": "Aero Town", "display_name": "Hyundai Aero Town", "vehicle_type": "Bus", "seat_count": 35, "sort_order": 122},
    {"brand": "Hyundai", "model_name": "Accent", "display_name": "Hyundai Accent", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 123},
    {"brand": "Hyundai", "model_name": "Elantra", "display_name": "Hyundai Elantra", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 124},
    {"brand": "Hyundai", "model_name": "Sonata", "display_name": "Hyundai Sonata", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 125},
    {"brand": "Hyundai", "model_name": "Grand i10", "display_name": "Hyundai Grand i10", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 126},
    {"brand": "Hyundai", "model_name": "Grand i10 Sedan", "display_name": "Hyundai Grand i10 Sedan", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 127},
    {"brand": "Hyundai", "model_name": "i20", "display_name": "Hyundai i20", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 128},
    {"brand": "Hyundai", "model_name": "i30", "display_name": "Hyundai i30", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 129},
    {"brand": "Hyundai", "model_name": "Santa Fe", "display_name": "Hyundai Santa Fe", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 130},
    {"brand": "Hyundai", "model_name": "Tucson", "display_name": "Hyundai Tucson", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 131},
    {"brand": "Hyundai", "model_name": "Palisade", "display_name": "Hyundai Palisade", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 132},
    {"brand": "Hyundai", "model_name": "Creta", "display_name": "Hyundai Creta", "vehicle_type": "Crossover", "seat_count": 4, "sort_order": 133},
    {"brand": "Hyundai", "model_name": "Venue", "display_name": "Hyundai Venue", "vehicle_type": "Compact SUV", "seat_count": 4, "sort_order": 134},
    {"brand": "Hyundai", "model_name": "Alcazar", "display_name": "Hyundai Alcazar", "vehicle_type": "7-Seat SUV", "seat_count": 7, "sort_order": 135},
    {"brand": "Hyundai", "model_name": "Custin", "display_name": "Hyundai Custin / Custo", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 136},
    {"brand": "Hyundai", "model_name": "Stargazer", "display_name": "Hyundai Stargazer", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 137},
    {"brand": "Hyundai", "model_name": "Ioniq 5", "display_name": "Hyundai Ioniq 5", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 138},
    {"brand": "Hyundai", "model_name": "Ioniq 6", "display_name": "Hyundai Ioniq 6", "vehicle_type": "Electric Sedan", "seat_count": 4, "sort_order": 139},
    {"brand": "Hyundai", "model_name": "Kona", "display_name": "Hyundai Kona", "vehicle_type": "Compact SUV", "seat_count": 4, "sort_order": 140},
    {"brand": "Hyundai", "model_name": "Kona Electric", "display_name": "Hyundai Kona Electric", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 141},
    {"brand": "Hyundai", "model_name": "Exter", "display_name": "Hyundai Exter", "vehicle_type": "Micro SUV", "seat_count": 4, "sort_order": 142},
    {"brand": "Hyundai", "model_name": "Aura", "display_name": "Hyundai Aura", "vehicle_type": "Compact Sedan", "seat_count": 4, "sort_order": 143},
    {"brand": "Hyundai", "model_name": "Grandeur", "display_name": "Hyundai Grandeur / Azera", "vehicle_type": "Luxury Sedan", "seat_count": 4, "sort_order": 144},
    {"brand": "Hyundai", "model_name": "Bayon", "display_name": "Hyundai Bayon", "vehicle_type": "Crossover", "seat_count": 4, "sort_order": 145},
    {"brand": "Hyundai", "model_name": "H350", "display_name": "Hyundai H350 Van", "vehicle_type": "Minibus", "seat_count": 16, "sort_order": 146},
    {"brand": "Hyundai", "model_name": "Genesis G80", "display_name": "Genesis G80", "vehicle_type": "Luxury Sedan", "seat_count": 4, "sort_order": 147},
    {"brand": "Hyundai", "model_name": "Genesis G90", "display_name": "Genesis G90", "vehicle_type": "VIP Luxury Sedan", "seat_count": 4, "sort_order": 148},
    {"brand": "Hyundai", "model_name": "Genesis GV80", "display_name": "Genesis GV80", "vehicle_type": "Luxury SUV", "seat_count": 7, "sort_order": 149},

    # --- 4. LEXUS (Luxury / Private Hire / SUV in Cambodia) ---
    {"brand": "Lexus", "model_name": "RX330", "display_name": "Lexus RX330", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 150},
    {"brand": "Lexus", "model_name": "RX350", "display_name": "Lexus RX350", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 151},
    {"brand": "Lexus", "model_name": "RX450h", "display_name": "Lexus RX450h", "vehicle_type": "Hybrid SUV", "seat_count": 4, "sort_order": 152},
    {"brand": "Lexus", "model_name": "RX500h", "display_name": "Lexus RX500h", "vehicle_type": "Luxury Hybrid SUV", "seat_count": 4, "sort_order": 153},
    {"brand": "Lexus", "model_name": "NX300", "display_name": "Lexus NX300", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 154},
    {"brand": "Lexus", "model_name": "NX350h", "display_name": "Lexus NX350h", "vehicle_type": "Hybrid SUV", "seat_count": 4, "sort_order": 155},
    {"brand": "Lexus", "model_name": "LX570", "display_name": "Lexus LX570", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 156},
    {"brand": "Lexus", "model_name": "LX600", "display_name": "Lexus LX600", "vehicle_type": "Luxury SUV", "seat_count": 7, "sort_order": 157},
    {"brand": "Lexus", "model_name": "GX460", "display_name": "Lexus GX460", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 158},
    {"brand": "Lexus", "model_name": "GX550", "display_name": "Lexus GX550", "vehicle_type": "Luxury SUV", "seat_count": 7, "sort_order": 159},
    {"brand": "Lexus", "model_name": "LM350h", "display_name": "Lexus LM350h", "vehicle_type": "Luxury MPV", "seat_count": 7, "sort_order": 160},
    {"brand": "Lexus", "model_name": "LM500h", "display_name": "Lexus LM500h", "vehicle_type": "VIP Luxury MPV", "seat_count": 4, "sort_order": 161},
    {"brand": "Lexus", "model_name": "ES300h", "display_name": "Lexus ES300h", "vehicle_type": "Luxury Hybrid Sedan", "seat_count": 4, "sort_order": 162},
    {"brand": "Lexus", "model_name": "ES350", "display_name": "Lexus ES350", "vehicle_type": "Luxury Sedan", "seat_count": 4, "sort_order": 163},
    {"brand": "Lexus", "model_name": "IS250", "display_name": "Lexus IS250", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 164},
    {"brand": "Lexus", "model_name": "IS300", "display_name": "Lexus IS300", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 165},
    {"brand": "Lexus", "model_name": "LS500", "display_name": "Lexus LS500", "vehicle_type": "VIP Luxury Sedan", "seat_count": 4, "sort_order": 166},
    {"brand": "Lexus", "model_name": "LS500h", "display_name": "Lexus LS500h", "vehicle_type": "VIP Hybrid Sedan", "seat_count": 4, "sort_order": 167},
    {"brand": "Lexus", "model_name": "TX", "display_name": "Lexus TX", "vehicle_type": "Luxury 3-Row SUV", "seat_count": 7, "sort_order": 168},
    {"brand": "Lexus", "model_name": "RZ450e", "display_name": "Lexus RZ450e", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 169},
    {"brand": "Lexus", "model_name": "UX250h", "display_name": "Lexus UX250h", "vehicle_type": "Compact Hybrid SUV", "seat_count": 4, "sort_order": 170},
    {"brand": "Lexus", "model_name": "LBX", "display_name": "Lexus LBX", "vehicle_type": "Urban Hybrid Crossover", "seat_count": 4, "sort_order": 171},

    # --- 5. KIA (Carnival, Sorento, Morning, Soluto, Buses) ---
    {"brand": "Kia", "model_name": "Carnival", "display_name": "Kia Carnival", "vehicle_type": "MPV / Minivan", "seat_count": 11, "sort_order": 172},
    {"brand": "Kia", "model_name": "Grand Carnival", "display_name": "Kia Grand Carnival", "vehicle_type": "MPV", "seat_count": 11, "sort_order": 173},
    {"brand": "Kia", "model_name": "Sorento", "display_name": "Kia Sorento", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 174},
    {"brand": "Kia", "model_name": "Morning", "display_name": "Kia Morning / Picanto", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 175},
    {"brand": "Kia", "model_name": "Soluto", "display_name": "Kia Soluto", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 176},
    {"brand": "Kia", "model_name": "K5", "display_name": "Kia K5", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 177},
    {"brand": "Kia", "model_name": "K3", "display_name": "Kia K3 / Cerato / Forte", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 178},
    {"brand": "Kia", "model_name": "Rio", "display_name": "Kia Rio", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 179},
    {"brand": "Kia", "model_name": "Carens", "display_name": "Kia Carens", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 180},
    {"brand": "Kia", "model_name": "Seltos", "display_name": "Kia Seltos", "vehicle_type": "Compact SUV", "seat_count": 4, "sort_order": 181},
    {"brand": "Kia", "model_name": "Sportage", "display_name": "Kia Sportage", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 182},
    {"brand": "Kia", "model_name": "Sonet", "display_name": "Kia Sonet", "vehicle_type": "Compact SUV", "seat_count": 4, "sort_order": 183},
    {"brand": "Kia", "model_name": "Telluride", "display_name": "Kia Telluride", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 184},
    {"brand": "Kia", "model_name": "EV6", "display_name": "Kia EV6", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 185},
    {"brand": "Kia", "model_name": "EV9", "display_name": "Kia EV9", "vehicle_type": "Electric 3-Row SUV", "seat_count": 7, "sort_order": 186},
    {"brand": "Kia", "model_name": "EV5", "display_name": "Kia EV5", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 187},
    {"brand": "Kia", "model_name": "EV3", "display_name": "Kia EV3", "vehicle_type": "Compact EV Crossover", "seat_count": 4, "sort_order": 188},
    {"brand": "Kia", "model_name": "Pegas", "display_name": "Kia Pegas", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 189},
    {"brand": "Kia", "model_name": "Ray", "display_name": "Kia Ray", "vehicle_type": "Box MPV", "seat_count": 4, "sort_order": 190},
    {"brand": "Kia", "model_name": "Ceed", "display_name": "Kia Ceed", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 191},
    {"brand": "Kia", "model_name": "K8", "display_name": "Kia K8", "vehicle_type": "Luxury Sedan", "seat_count": 4, "sort_order": 192},
    {"brand": "Kia", "model_name": "K9", "display_name": "Kia K9 / K900", "vehicle_type": "VIP Luxury Sedan", "seat_count": 4, "sort_order": 193},
    {"brand": "Kia", "model_name": "Granbird", "display_name": "Kia Granbird Bus", "vehicle_type": "Coach Bus", "seat_count": 45, "sort_order": 194},
    {"brand": "Kia", "model_name": "Bongo", "display_name": "Kia Bongo Passenger", "vehicle_type": "Passenger Van", "seat_count": 12, "sort_order": 195},

    # --- 6. FORD (Transit, Everest, Ranger, Tourneo) ---
    {"brand": "Ford", "model_name": "Transit", "display_name": "Ford Transit", "vehicle_type": "Van", "seat_count": 16, "sort_order": 196},
    {"brand": "Ford", "model_name": "Tourneo Custom", "display_name": "Ford Tourneo Custom", "vehicle_type": "VIP Passenger Van", "seat_count": 9, "sort_order": 197},
    {"brand": "Ford", "model_name": "Everest", "display_name": "Ford Everest", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 198},
    {"brand": "Ford", "model_name": "Territory", "display_name": "Ford Territory", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 199},
    {"brand": "Ford", "model_name": "Explorer", "display_name": "Ford Explorer", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 200},
    {"brand": "Ford", "model_name": "Expedition", "display_name": "Ford Expedition", "vehicle_type": "Luxury 8-Seat SUV", "seat_count": 8, "sort_order": 201},
    {"brand": "Ford", "model_name": "Ranger", "display_name": "Ford Ranger", "vehicle_type": "Pickup", "seat_count": 4, "sort_order": 202},
    {"brand": "Ford", "model_name": "Ranger Raptor", "display_name": "Ford Ranger Raptor", "vehicle_type": "Pickup", "seat_count": 4, "sort_order": 203},
    {"brand": "Ford", "model_name": "F-150", "display_name": "Ford F-150", "vehicle_type": "Pickup", "seat_count": 4, "sort_order": 204},
    {"brand": "Ford", "model_name": "Taurus", "display_name": "Ford Taurus", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 205},
    {"brand": "Ford", "model_name": "Mondeo", "display_name": "Ford Mondeo", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 206},
    {"brand": "Ford", "model_name": "Focus", "display_name": "Ford Focus", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 207},
    {"brand": "Ford", "model_name": "Escape", "display_name": "Ford Escape / Kuga", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 208},
    {"brand": "Ford", "model_name": "EcoSport", "display_name": "Ford EcoSport", "vehicle_type": "Compact SUV", "seat_count": 4, "sort_order": 209},
    {"brand": "Ford", "model_name": "Mustang Mach-E", "display_name": "Ford Mustang Mach-E", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 210},

    # --- 7. MITSUBISHI (Xpander, Pajero Sport, Triton, Attrage) ---
    {"brand": "Mitsubishi", "model_name": "Xpander", "display_name": "Mitsubishi Xpander", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 211},
    {"brand": "Mitsubishi", "model_name": "Xpander Cross", "display_name": "Mitsubishi Xpander Cross", "vehicle_type": "Crossover MPV", "seat_count": 7, "sort_order": 212},
    {"brand": "Mitsubishi", "model_name": "Pajero Sport", "display_name": "Mitsubishi Pajero Sport", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 213},
    {"brand": "Mitsubishi", "model_name": "Outlander", "display_name": "Mitsubishi Outlander", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 214},
    {"brand": "Mitsubishi", "model_name": "Attrage", "display_name": "Mitsubishi Attrage", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 215},
    {"brand": "Mitsubishi", "model_name": "Mirage", "display_name": "Mitsubishi Mirage", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 216},
    {"brand": "Mitsubishi", "model_name": "Triton", "display_name": "Mitsubishi Triton", "vehicle_type": "Pickup", "seat_count": 4, "sort_order": 217},
    {"brand": "Mitsubishi", "model_name": "Xforce", "display_name": "Mitsubishi Xforce", "vehicle_type": "Compact SUV", "seat_count": 4, "sort_order": 218},
    {"brand": "Mitsubishi", "model_name": "Delica D:5", "display_name": "Mitsubishi Delica D:5", "vehicle_type": "4WD MPV", "seat_count": 8, "sort_order": 219},
    {"brand": "Mitsubishi", "model_name": "Rosa", "display_name": "Mitsubishi Fuso Rosa", "vehicle_type": "Minibus", "seat_count": 29, "sort_order": 220},
    {"brand": "Mitsubishi", "model_name": "Eclipse Cross", "display_name": "Mitsubishi Eclipse Cross", "vehicle_type": "Crossover", "seat_count": 4, "sort_order": 221},
    {"brand": "Mitsubishi", "model_name": "Grandis", "display_name": "Mitsubishi Grandis", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 222},
    {"brand": "Mitsubishi", "model_name": "Lancer", "display_name": "Mitsubishi Lancer", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 223},

    # --- 8. HONDA (City, Civic, Accord, CR-V, HR-V, Odyssey, StepWGN) ---
    {"brand": "Honda", "model_name": "City", "display_name": "Honda City", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 224},
    {"brand": "Honda", "model_name": "Civic", "display_name": "Honda Civic", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 225},
    {"brand": "Honda", "model_name": "Accord", "display_name": "Honda Accord", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 226},
    {"brand": "Honda", "model_name": "CR-V", "display_name": "Honda CR-V", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 227},
    {"brand": "Honda", "model_name": "HR-V", "display_name": "Honda HR-V", "vehicle_type": "Crossover", "seat_count": 4, "sort_order": 228},
    {"brand": "Honda", "model_name": "BR-V", "display_name": "Honda BR-V", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 229},
    {"brand": "Honda", "model_name": "WR-V", "display_name": "Honda WR-V", "vehicle_type": "Compact SUV", "seat_count": 4, "sort_order": 230},
    {"brand": "Honda", "model_name": "Odyssey", "display_name": "Honda Odyssey", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 231},
    {"brand": "Honda", "model_name": "StepWGN", "display_name": "Honda StepWGN", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 232},
    {"brand": "Honda", "model_name": "Freed", "display_name": "Honda Freed", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 233},
    {"brand": "Honda", "model_name": "Mobilio", "display_name": "Honda Mobilio", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 234},
    {"brand": "Honda", "model_name": "Fit", "display_name": "Honda Fit / Jazz", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 235},
    {"brand": "Honda", "model_name": "Brio", "display_name": "Honda Brio", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 236},
    {"brand": "Honda", "model_name": "Amaze", "display_name": "Honda Amaze", "vehicle_type": "Compact Sedan", "seat_count": 4, "sort_order": 237},
    {"brand": "Honda", "model_name": "Elevate", "display_name": "Honda Elevate", "vehicle_type": "Compact SUV", "seat_count": 4, "sort_order": 238},
    {"brand": "Honda", "model_name": "Pilot", "display_name": "Honda Pilot", "vehicle_type": "8-Seat SUV", "seat_count": 8, "sort_order": 239},
    {"brand": "Honda", "model_name": "Elysion", "display_name": "Honda Elysion", "vehicle_type": "Luxury MPV", "seat_count": 7, "sort_order": 240},
    {"brand": "Honda", "model_name": "ZR-V", "display_name": "Honda ZR-V", "vehicle_type": "Crossover", "seat_count": 4, "sort_order": 241},

    # --- 9. NISSAN (Almera, NV200 Taxi, Serena, Urvan, Navara, Terra) ---
    {"brand": "Nissan", "model_name": "Almera", "display_name": "Nissan Almera", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 242},
    {"brand": "Nissan", "model_name": "NV200", "display_name": "Nissan NV200 Taxi", "vehicle_type": "Taxi Van", "seat_count": 5, "sort_order": 243},
    {"brand": "Nissan", "model_name": "Serena", "display_name": "Nissan Serena", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 244},
    {"brand": "Nissan", "model_name": "Urvan", "display_name": "Nissan Urvan", "vehicle_type": "Van", "seat_count": 15, "sort_order": 245},
    {"brand": "Nissan", "model_name": "Caravan", "display_name": "Nissan NV350 Caravan", "vehicle_type": "Van", "seat_count": 15, "sort_order": 246},
    {"brand": "Nissan", "model_name": "Civilian", "display_name": "Nissan Civilian Bus", "vehicle_type": "Minibus", "seat_count": 29, "sort_order": 247},
    {"brand": "Nissan", "model_name": "Navara", "display_name": "Nissan Navara", "vehicle_type": "Pickup", "seat_count": 4, "sort_order": 248},
    {"brand": "Nissan", "model_name": "Terra", "display_name": "Nissan Terra", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 249},
    {"brand": "Nissan", "model_name": "Kicks e-POWER", "display_name": "Nissan Kicks e-POWER", "vehicle_type": "Compact SUV", "seat_count": 4, "sort_order": 250},
    {"brand": "Nissan", "model_name": "Sunny", "display_name": "Nissan Sunny / Versa", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 251},
    {"brand": "Nissan", "model_name": "Sentra", "display_name": "Nissan Sentra / Sylphy", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 252},
    {"brand": "Nissan", "model_name": "Altima", "display_name": "Nissan Altima / Teana", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 253},
    {"brand": "Nissan", "model_name": "Patrol", "display_name": "Nissan Patrol", "vehicle_type": "Luxury SUV", "seat_count": 7, "sort_order": 254},
    {"brand": "Nissan", "model_name": "X-Trail", "display_name": "Nissan X-Trail / Rogue", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 255},
    {"brand": "Nissan", "model_name": "Qashqai", "display_name": "Nissan Qashqai", "vehicle_type": "Crossover", "seat_count": 4, "sort_order": 256},
    {"brand": "Nissan", "model_name": "Leaf", "display_name": "Nissan Leaf", "vehicle_type": "Electric Hatchback", "seat_count": 4, "sort_order": 257},
    {"brand": "Nissan", "model_name": "Note e-POWER", "display_name": "Nissan Note e-POWER", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 258},
    {"brand": "Nissan", "model_name": "Livina", "display_name": "Nissan Livina", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 259},
    {"brand": "Nissan", "model_name": "Elgrand", "display_name": "Nissan Elgrand", "vehicle_type": "Luxury VIP MPV", "seat_count": 7, "sort_order": 260},
    {"brand": "Nissan", "model_name": "Ariya", "display_name": "Nissan Ariya", "vehicle_type": "Electric Crossover", "seat_count": 4, "sort_order": 261},
    {"brand": "Nissan", "model_name": "Pathfinder", "display_name": "Nissan Pathfinder", "vehicle_type": "3-Row SUV", "seat_count": 8, "sort_order": 262},

    # --- 10. MG (ZS, MG5, HS, Maxus 9, MG4) ---
    {"brand": "MG", "model_name": "ZS", "display_name": "MG ZS", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 263},
    {"brand": "MG", "model_name": "MG 5", "display_name": "MG 5", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 264},
    {"brand": "MG", "model_name": "HS", "display_name": "MG HS", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 265},
    {"brand": "MG", "model_name": "Maxus 9", "display_name": "MG Maxus 9", "vehicle_type": "Electric VIP MPV", "seat_count": 7, "sort_order": 266},
    {"brand": "MG", "model_name": "MG 4 EV", "display_name": "MG 4 EV", "vehicle_type": "Electric Hatchback", "seat_count": 4, "sort_order": 267},
    {"brand": "MG", "model_name": "MG 3", "display_name": "MG 3 Hybrid", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 268},
    {"brand": "MG", "model_name": "MG GT", "display_name": "MG GT", "vehicle_type": "Fastback Sedan", "seat_count": 4, "sort_order": 269},
    {"brand": "MG", "model_name": "MG 7", "display_name": "MG 7", "vehicle_type": "Executive Fastback", "seat_count": 4, "sort_order": 270},
    {"brand": "MG", "model_name": "MG One", "display_name": "MG One", "vehicle_type": "Crossover SUV", "seat_count": 4, "sort_order": 271},
    {"brand": "MG", "model_name": "ZS EV", "display_name": "MG ZS EV", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 272},
    {"brand": "MG", "model_name": "Hector", "display_name": "MG Hector", "vehicle_type": "SUV", "seat_count": 6, "sort_order": 273},
    {"brand": "MG", "model_name": "Gloster", "display_name": "MG Gloster", "vehicle_type": "Luxury 7-Seat SUV", "seat_count": 7, "sort_order": 274},
    {"brand": "MG", "model_name": "Extender", "display_name": "MG Extender", "vehicle_type": "Pickup", "seat_count": 4, "sort_order": 275},

    # --- 11. GEELY & ZEEKR (Coolray, Emgrand, Monjaro, Okavango, Zeekr) ---
    {"brand": "Geely", "model_name": "Coolray", "display_name": "Geely Coolray", "vehicle_type": "Crossover", "seat_count": 4, "sort_order": 276},
    {"brand": "Geely", "model_name": "Monjaro", "display_name": "Geely Monjaro", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 277},
    {"brand": "Geely", "model_name": "Emgrand", "display_name": "Geely Emgrand", "vehicle_type": "Sedan Taxi", "seat_count": 4, "sort_order": 278},
    {"brand": "Geely", "model_name": "Okavango", "display_name": "Geely Okavango", "vehicle_type": "7-Seat SUV", "seat_count": 7, "sort_order": 279},
    {"brand": "Geely", "model_name": "Azkarra", "display_name": "Geely Azkarra", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 280},
    {"brand": "Geely", "model_name": "Geometry C", "display_name": "Geely Geometry C", "vehicle_type": "Electric Crossover", "seat_count": 4, "sort_order": 281},
    {"brand": "Geely", "model_name": "Preface", "display_name": "Geely Preface", "vehicle_type": "Luxury Sedan", "seat_count": 4, "sort_order": 282},
    {"brand": "Geely", "model_name": "Boyue L", "display_name": "Geely Boyue L", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 283},
    {"brand": "Geely", "model_name": "Galaxy L7", "display_name": "Geely Galaxy L7 PHEV", "vehicle_type": "Hybrid SUV", "seat_count": 4, "sort_order": 284},
    {"brand": "Geely", "model_name": "Galaxy E8", "display_name": "Geely Galaxy E8", "vehicle_type": "Electric Executive Sedan", "seat_count": 4, "sort_order": 285},
    {"brand": "Geely", "model_name": "Panda Mini", "display_name": "Geely Panda Mini EV", "vehicle_type": "City EV", "seat_count": 4, "sort_order": 286},
    {"brand": "Zeekr", "model_name": "001", "display_name": "Zeekr 001", "vehicle_type": "Electric Luxury Shooting Brake", "seat_count": 4, "sort_order": 287},
    {"brand": "Zeekr", "model_name": "009", "display_name": "Zeekr 009 VIP MPV", "vehicle_type": "Ultra-Luxury Electric MPV", "seat_count": 6, "sort_order": 288},
    {"brand": "Zeekr", "model_name": "X", "display_name": "Zeekr X", "vehicle_type": "Electric Urban SUV", "seat_count": 4, "sort_order": 289},
    {"brand": "Zeekr", "model_name": "007", "display_name": "Zeekr 007", "vehicle_type": "Electric Luxury Sedan", "seat_count": 4, "sort_order": 290},

    # --- 12. MERCEDES-BENZ (Luxury Taxi / Chauffeur / VIP Vans) ---
    {"brand": "Mercedes-Benz", "model_name": "E-Class", "display_name": "Mercedes-Benz E-Class", "vehicle_type": "Luxury Sedan", "seat_count": 4, "sort_order": 291},
    {"brand": "Mercedes-Benz", "model_name": "S-Class", "display_name": "Mercedes-Benz S-Class", "vehicle_type": "VIP Luxury Sedan", "seat_count": 4, "sort_order": 292},
    {"brand": "Mercedes-Benz", "model_name": "C-Class", "display_name": "Mercedes-Benz C-Class", "vehicle_type": "Luxury Sedan", "seat_count": 4, "sort_order": 293},
    {"brand": "Mercedes-Benz", "model_name": "GLC", "display_name": "Mercedes-Benz GLC", "vehicle_type": "Luxury SUV", "seat_count": 4, "sort_order": 294},
    {"brand": "Mercedes-Benz", "model_name": "GLE", "display_name": "Mercedes-Benz GLE", "vehicle_type": "Luxury SUV", "seat_count": 7, "sort_order": 295},
    {"brand": "Mercedes-Benz", "model_name": "GLS", "display_name": "Mercedes-Benz GLS", "vehicle_type": "Luxury 7-Seat SUV", "seat_count": 7, "sort_order": 296},
    {"brand": "Mercedes-Benz", "model_name": "V-Class", "display_name": "Mercedes-Benz V-Class", "vehicle_type": "VIP Van", "seat_count": 7, "sort_order": 297},
    {"brand": "Mercedes-Benz", "model_name": "Vito", "display_name": "Mercedes-Benz Vito Tourer", "vehicle_type": "Passenger Van", "seat_count": 9, "sort_order": 298},
    {"brand": "Mercedes-Benz", "model_name": "Sprinter", "display_name": "Mercedes-Benz Sprinter", "vehicle_type": "Minibus", "seat_count": 16, "sort_order": 299},
    {"brand": "Mercedes-Benz", "model_name": "EQV", "display_name": "Mercedes-Benz EQV", "vehicle_type": "Electric VIP MPV", "seat_count": 7, "sort_order": 300},
    {"brand": "Mercedes-Benz", "model_name": "EQE", "display_name": "Mercedes-Benz EQE", "vehicle_type": "Electric Luxury Sedan", "seat_count": 4, "sort_order": 301},
    {"brand": "Mercedes-Benz", "model_name": "EQS", "display_name": "Mercedes-Benz EQS", "vehicle_type": "Electric VIP Sedan", "seat_count": 4, "sort_order": 302},
    {"brand": "Mercedes-Benz", "model_name": "G-Class", "display_name": "Mercedes-Benz G-Class", "vehicle_type": "Luxury SUV", "seat_count": 4, "sort_order": 303},
    {"brand": "Mercedes-Benz", "model_name": "A-Class Sedan", "display_name": "Mercedes-Benz A-Class Sedan", "vehicle_type": "Compact Luxury Sedan", "seat_count": 4, "sort_order": 304},
    {"brand": "Mercedes-Benz", "model_name": "GLB", "display_name": "Mercedes-Benz GLB", "vehicle_type": "7-Seat Compact SUV", "seat_count": 7, "sort_order": 305},

    # --- 13. BMW (Chauffeur, Executive, SUV) ---
    {"brand": "BMW", "model_name": "5 Series", "display_name": "BMW 5 Series", "vehicle_type": "Luxury Sedan", "seat_count": 4, "sort_order": 306},
    {"brand": "BMW", "model_name": "7 Series", "display_name": "BMW 7 Series", "vehicle_type": "VIP Luxury Sedan", "seat_count": 4, "sort_order": 307},
    {"brand": "BMW", "model_name": "3 Series", "display_name": "BMW 3 Series", "vehicle_type": "Luxury Sedan", "seat_count": 4, "sort_order": 308},
    {"brand": "BMW", "model_name": "X5", "display_name": "BMW X5", "vehicle_type": "Luxury SUV", "seat_count": 7, "sort_order": 309},
    {"brand": "BMW", "model_name": "X7", "display_name": "BMW X7", "vehicle_type": "Luxury SUV", "seat_count": 7, "sort_order": 310},
    {"brand": "BMW", "model_name": "X3", "display_name": "BMW X3", "vehicle_type": "Luxury SUV", "seat_count": 4, "sort_order": 311},
    {"brand": "BMW", "model_name": "X1", "display_name": "BMW X1", "vehicle_type": "Compact Luxury SUV", "seat_count": 4, "sort_order": 312},
    {"brand": "BMW", "model_name": "i4", "display_name": "BMW i4", "vehicle_type": "Electric Sedan", "seat_count": 4, "sort_order": 313},
    {"brand": "BMW", "model_name": "i7", "display_name": "BMW i7", "vehicle_type": "Electric VIP Sedan", "seat_count": 4, "sort_order": 314},
    {"brand": "BMW", "model_name": "iX", "display_name": "BMW iX", "vehicle_type": "Electric Luxury SUV", "seat_count": 4, "sort_order": 315},
    {"brand": "BMW", "model_name": "2 Series Gran Tourer", "display_name": "BMW 2 Series Gran Tourer", "vehicle_type": "7-Seat MPV", "seat_count": 7, "sort_order": 316},

    # --- 14. AUDI ---
    {"brand": "Audi", "model_name": "A6", "display_name": "Audi A6", "vehicle_type": "Luxury Sedan", "seat_count": 4, "sort_order": 317},
    {"brand": "Audi", "model_name": "A8", "display_name": "Audi A8", "vehicle_type": "VIP Luxury Sedan", "seat_count": 4, "sort_order": 318},
    {"brand": "Audi", "model_name": "A4", "display_name": "Audi A4", "vehicle_type": "Luxury Sedan", "seat_count": 4, "sort_order": 319},
    {"brand": "Audi", "model_name": "Q7", "display_name": "Audi Q7", "vehicle_type": "Luxury 7-Seat SUV", "seat_count": 7, "sort_order": 320},
    {"brand": "Audi", "model_name": "Q5", "display_name": "Audi Q5", "vehicle_type": "Luxury SUV", "seat_count": 4, "sort_order": 321},
    {"brand": "Audi", "model_name": "Q8", "display_name": "Audi Q8", "vehicle_type": "Luxury Coupe SUV", "seat_count": 4, "sort_order": 322},
    {"brand": "Audi", "model_name": "e-tron", "display_name": "Audi e-tron / Q8 e-tron", "vehicle_type": "Electric Luxury SUV", "seat_count": 4, "sort_order": 323},
    {"brand": "Audi", "model_name": "A3 Sedan", "display_name": "Audi A3 Sedan", "vehicle_type": "Compact Luxury Sedan", "seat_count": 4, "sort_order": 324},

    # --- 15. TESLA ---
    {"brand": "Tesla", "model_name": "Model 3", "display_name": "Tesla Model 3", "vehicle_type": "Electric Sedan", "seat_count": 4, "sort_order": 325},
    {"brand": "Tesla", "model_name": "Model Y", "display_name": "Tesla Model Y", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 326},
    {"brand": "Tesla", "model_name": "Model S", "display_name": "Tesla Model S", "vehicle_type": "Electric Luxury Sedan", "seat_count": 4, "sort_order": 327},
    {"brand": "Tesla", "model_name": "Model X", "display_name": "Tesla Model X", "vehicle_type": "Electric Luxury SUV", "seat_count": 7, "sort_order": 328},
    {"brand": "Tesla", "model_name": "Cybertruck", "display_name": "Tesla Cybertruck", "vehicle_type": "Electric Pickup", "seat_count": 5, "sort_order": 329},

    # --- 16. VOLKSWAGEN (Caravelle, Crafter, Jetta, Passat, ID.4, Multivan) ---
    {"brand": "Volkswagen", "model_name": "Caravelle", "display_name": "Volkswagen Caravelle", "vehicle_type": "VIP Van", "seat_count": 9, "sort_order": 330},
    {"brand": "Volkswagen", "model_name": "Multivan", "display_name": "Volkswagen Multivan T7", "vehicle_type": "VIP MPV", "seat_count": 7, "sort_order": 331},
    {"brand": "Volkswagen", "model_name": "Transporter", "display_name": "Volkswagen Transporter Shuttle", "vehicle_type": "Passenger Van", "seat_count": 9, "sort_order": 332},
    {"brand": "Volkswagen", "model_name": "Crafter", "display_name": "Volkswagen Crafter Minibus", "vehicle_type": "Minibus", "seat_count": 16, "sort_order": 333},
    {"brand": "Volkswagen", "model_name": "Caddy", "display_name": "Volkswagen Caddy Maxi Taxi", "vehicle_type": "Taxi Van", "seat_count": 7, "sort_order": 334},
    {"brand": "Volkswagen", "model_name": "Touran", "display_name": "Volkswagen Touran", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 335},
    {"brand": "Volkswagen", "model_name": "Passat", "display_name": "Volkswagen Passat", "vehicle_type": "Sedan Taxi", "seat_count": 4, "sort_order": 336},
    {"brand": "Volkswagen", "model_name": "Jetta", "display_name": "Volkswagen Jetta", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 337},
    {"brand": "Volkswagen", "model_name": "Lavida", "display_name": "Volkswagen Lavida Taxi", "vehicle_type": "Sedan Taxi", "seat_count": 4, "sort_order": 338},
    {"brand": "Volkswagen", "model_name": "Santana", "display_name": "Volkswagen Santana Taxi", "vehicle_type": "Classic Taxi Sedan", "seat_count": 4, "sort_order": 339},
    {"brand": "Volkswagen", "model_name": "Tiguan", "display_name": "Volkswagen Tiguan Allspace", "vehicle_type": "7-Seat SUV", "seat_count": 7, "sort_order": 340},
    {"brand": "Volkswagen", "model_name": "Teramont", "display_name": "Volkswagen Teramont / Atlas", "vehicle_type": "3-Row SUV", "seat_count": 7, "sort_order": 341},
    {"brand": "Volkswagen", "model_name": "ID.4", "display_name": "Volkswagen ID.4", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 342},
    {"brand": "Volkswagen", "model_name": "ID. Buzz", "display_name": "Volkswagen ID. Buzz", "vehicle_type": "Electric VIP MPV", "seat_count": 7, "sort_order": 343},
    {"brand": "Volkswagen", "model_name": "ID.7", "display_name": "Volkswagen ID.7", "vehicle_type": "Electric Executive Sedan", "seat_count": 4, "sort_order": 344},
    {"brand": "Volkswagen", "model_name": "Golf", "display_name": "Volkswagen Golf", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 345},
    {"brand": "Volkswagen", "model_name": "Polo Sedan", "display_name": "Volkswagen Polo Sedan / Virtus", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 346},
    {"brand": "Volkswagen", "model_name": "T-Cross", "display_name": "Volkswagen T-Cross / Taigun", "vehicle_type": "Compact SUV", "seat_count": 4, "sort_order": 347},

    # --- 17. SKODA (Octavia, Superb, Kodiaq) ---
    {"brand": "Skoda", "model_name": "Octavia", "display_name": "Skoda Octavia", "vehicle_type": "Sedan Taxi", "seat_count": 4, "sort_order": 348},
    {"brand": "Skoda", "model_name": "Superb", "display_name": "Skoda Superb", "vehicle_type": "Luxury Sedan Taxi", "seat_count": 4, "sort_order": 349},
    {"brand": "Skoda", "model_name": "Kodiaq", "display_name": "Skoda Kodiaq", "vehicle_type": "7-Seat SUV", "seat_count": 7, "sort_order": 350},
    {"brand": "Skoda", "model_name": "Karoq", "display_name": "Skoda Karoq", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 351},
    {"brand": "Skoda", "model_name": "Kamiq", "display_name": "Skoda Kamiq", "vehicle_type": "Compact SUV", "seat_count": 4, "sort_order": 352},
    {"brand": "Skoda", "model_name": "Slavia", "display_name": "Skoda Slavia", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 353},
    {"brand": "Skoda", "model_name": "Kushaq", "display_name": "Skoda Kushaq", "vehicle_type": "Compact SUV", "seat_count": 4, "sort_order": 354},
    {"brand": "Skoda", "model_name": "Fabia", "display_name": "Skoda Fabia", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 355},
    {"brand": "Skoda", "model_name": "Enyaq iV", "display_name": "Skoda Enyaq iV", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 356},

    # --- 18. SUZUKI (Ertiga, XL7, APV, Swift, Ciaz, Dzire) ---
    {"brand": "Suzuki", "model_name": "Ertiga", "display_name": "Suzuki Ertiga Hybrid", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 357},
    {"brand": "Suzuki", "model_name": "XL7", "display_name": "Suzuki XL7", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 358},
    {"brand": "Suzuki", "model_name": "APV", "display_name": "Suzuki APV", "vehicle_type": "Van", "seat_count": 8, "sort_order": 359},
    {"brand": "Suzuki", "model_name": "Swift", "display_name": "Suzuki Swift", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 360},
    {"brand": "Suzuki", "model_name": "Ciaz", "display_name": "Suzuki Ciaz", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 361},
    {"brand": "Suzuki", "model_name": "Dzire", "display_name": "Suzuki Dzire Taxi", "vehicle_type": "Sedan Taxi", "seat_count": 4, "sort_order": 362},
    {"brand": "Suzuki", "model_name": "Baleno", "display_name": "Suzuki Baleno", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 363},
    {"brand": "Suzuki", "model_name": "Celerio", "display_name": "Suzuki Celerio", "vehicle_type": "City Car", "seat_count": 4, "sort_order": 364},
    {"brand": "Suzuki", "model_name": "S-Presso", "display_name": "Suzuki S-Presso", "vehicle_type": "Micro SUV", "seat_count": 4, "sort_order": 365},
    {"brand": "Suzuki", "model_name": "Grand Vitara", "display_name": "Suzuki Grand Vitara Hybrid", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 366},
    {"brand": "Suzuki", "model_name": "Brezza", "display_name": "Suzuki Brezza", "vehicle_type": "Compact SUV", "seat_count": 4, "sort_order": 367},
    {"brand": "Suzuki", "model_name": "Every", "display_name": "Suzuki Every Van", "vehicle_type": "Micro Van", "seat_count": 4, "sort_order": 368},
    {"brand": "Suzuki", "model_name": "Jimny 5-Door", "display_name": "Suzuki Jimny 5-Door", "vehicle_type": "Compact 4x4", "seat_count": 4, "sort_order": 369},

    # --- 19. PEUGEOT ---
    {"brand": "Peugeot", "model_name": "301", "display_name": "Peugeot 301 Taxi", "vehicle_type": "Sedan Taxi", "seat_count": 4, "sort_order": 370},
    {"brand": "Peugeot", "model_name": "508", "display_name": "Peugeot 508", "vehicle_type": "Luxury Sedan", "seat_count": 4, "sort_order": 371},
    {"brand": "Peugeot", "model_name": "3008", "display_name": "Peugeot 3008", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 372},
    {"brand": "Peugeot", "model_name": "5008", "display_name": "Peugeot 5008", "vehicle_type": "7-Seat SUV", "seat_count": 7, "sort_order": 373},
    {"brand": "Peugeot", "model_name": "408", "display_name": "Peugeot 408 Fastback", "vehicle_type": "Crossover Sedan", "seat_count": 4, "sort_order": 374},
    {"brand": "Peugeot", "model_name": "2008", "display_name": "Peugeot 2008", "vehicle_type": "Compact SUV", "seat_count": 4, "sort_order": 375},
    {"brand": "Peugeot", "model_name": "Traveller", "display_name": "Peugeot Traveller VIP", "vehicle_type": "VIP Van", "seat_count": 8, "sort_order": 376},
    {"brand": "Peugeot", "model_name": "Rifter", "display_name": "Peugeot Rifter", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 377},
    {"brand": "Peugeot", "model_name": "Expert Combi", "display_name": "Peugeot Expert Combi", "vehicle_type": "Passenger Van", "seat_count": 9, "sort_order": 378},

    # --- 20. RENAULT & DACIA ---
    {"brand": "Renault", "model_name": "Logan", "display_name": "Renault Logan Taxi", "vehicle_type": "Sedan Taxi", "seat_count": 4, "sort_order": 379},
    {"brand": "Renault", "model_name": "Megane", "display_name": "Renault Megane", "vehicle_type": "Sedan / Hatchback", "seat_count": 4, "sort_order": 380},
    {"brand": "Renault", "model_name": "Duster", "display_name": "Renault Duster", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 381},
    {"brand": "Renault", "model_name": "Trafic", "display_name": "Renault Trafic Passenger", "vehicle_type": "Passenger Van", "seat_count": 9, "sort_order": 382},
    {"brand": "Renault", "model_name": "Master", "display_name": "Renault Master Minibus", "vehicle_type": "Minibus", "seat_count": 16, "sort_order": 383},
    {"brand": "Renault", "model_name": "Espace", "display_name": "Renault Espace", "vehicle_type": "7-Seat SUV", "seat_count": 7, "sort_order": 384},
    {"brand": "Renault", "model_name": "Kwid", "display_name": "Renault Kwid", "vehicle_type": "City Car", "seat_count": 4, "sort_order": 385},
    {"brand": "Renault", "model_name": "Triber", "display_name": "Renault Triber", "vehicle_type": "Compact 7-Seat MPV", "seat_count": 7, "sort_order": 386},
    {"brand": "Dacia", "model_name": "Jogger", "display_name": "Dacia Jogger", "vehicle_type": "7-Seat MPV", "seat_count": 7, "sort_order": 387},
    {"brand": "Dacia", "model_name": "Sandero", "display_name": "Dacia Sandero", "vehicle_type": "Hatchback", "seat_count": 4, "sort_order": 388},
    {"brand": "Dacia", "model_name": "Lodgy", "display_name": "Dacia Lodgy Taxi", "vehicle_type": "7-Seat Taxi MPV", "seat_count": 7, "sort_order": 389},

    # --- 21. CHEVROLET ---
    {"brand": "Chevrolet", "model_name": "Cruze", "display_name": "Chevrolet Cruze", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 390},
    {"brand": "Chevrolet", "model_name": "Malibu", "display_name": "Chevrolet Malibu", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 391},
    {"brand": "Chevrolet", "model_name": "Suburban", "display_name": "Chevrolet Suburban", "vehicle_type": "Luxury 8-Seat SUV", "seat_count": 8, "sort_order": 392},
    {"brand": "Chevrolet", "model_name": "Tahoe", "display_name": "Chevrolet Tahoe", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 393},
    {"brand": "Chevrolet", "model_name": "Trailblazer", "display_name": "Chevrolet Trailblazer", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 394},
    {"brand": "Chevrolet", "model_name": "Captiva", "display_name": "Chevrolet Captiva", "vehicle_type": "7-Seat SUV", "seat_count": 7, "sort_order": 395},
    {"brand": "Chevrolet", "model_name": "Colorado", "display_name": "Chevrolet Colorado", "vehicle_type": "Pickup", "seat_count": 4, "sort_order": 396},
    {"brand": "Chevrolet", "model_name": "Express", "display_name": "Chevrolet Express Passenger", "vehicle_type": "Passenger Van", "seat_count": 15, "sort_order": 397},
    {"brand": "Chevrolet", "model_name": "Aveo", "display_name": "Chevrolet Aveo / Sonic", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 398},
    {"brand": "Chevrolet", "model_name": "Traverse", "display_name": "Chevrolet Traverse", "vehicle_type": "3-Row SUV", "seat_count": 8, "sort_order": 399},

    # --- 22. WULING (Popular MPVs & Vans) ---
    {"brand": "Wuling", "model_name": "Hongguang S", "display_name": "Wuling Hongguang S", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 400},
    {"brand": "Wuling", "model_name": "Hongguang Plus", "display_name": "Wuling Hongguang Plus", "vehicle_type": "MPV", "seat_count": 8, "sort_order": 401},
    {"brand": "Wuling", "model_name": "Sunshine", "display_name": "Wuling Sunshine", "vehicle_type": "Van", "seat_count": 8, "sort_order": 402},
    {"brand": "Wuling", "model_name": "Cortez", "display_name": "Wuling Cortez", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 403},
    {"brand": "Wuling", "model_name": "Confero", "display_name": "Wuling Confero S", "vehicle_type": "MPV", "seat_count": 8, "sort_order": 404},
    {"brand": "Wuling", "model_name": "Almaz", "display_name": "Wuling Almaz Hybrid", "vehicle_type": "7-Seat SUV", "seat_count": 7, "sort_order": 405},
    {"brand": "Wuling", "model_name": "Formo", "display_name": "Wuling Formo Max", "vehicle_type": "Passenger Van", "seat_count": 8, "sort_order": 406},
    {"brand": "Wuling", "model_name": "Air EV", "display_name": "Wuling Air EV", "vehicle_type": "Micro EV", "seat_count": 4, "sort_order": 407},
    {"brand": "Wuling", "model_name": "Binguo EV", "display_name": "Wuling Binguo EV", "vehicle_type": "Electric Hatchback", "seat_count": 4, "sort_order": 408},
    {"brand": "Wuling", "model_name": "Cloud EV", "display_name": "Wuling Cloud EV", "vehicle_type": "Electric MPV", "seat_count": 5, "sort_order": 409},

    # --- 23. CHANGAN / DEEPAL / AVATR ---
    {"brand": "Changan", "model_name": "Alsvin", "display_name": "Changan Alsvin Taxi", "vehicle_type": "Sedan Taxi", "seat_count": 4, "sort_order": 410},
    {"brand": "Changan", "model_name": "CS35 Plus", "display_name": "Changan CS35 Plus", "vehicle_type": "Compact SUV", "seat_count": 4, "sort_order": 411},
    {"brand": "Changan", "model_name": "CS55 Plus", "display_name": "Changan CS55 Plus", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 412},
    {"brand": "Changan", "model_name": "CS75 Plus", "display_name": "Changan CS75 Plus", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 413},
    {"brand": "Changan", "model_name": "CS85", "display_name": "Changan CS85 Coupe", "vehicle_type": "Coupe SUV", "seat_count": 4, "sort_order": 414},
    {"brand": "Changan", "model_name": "CS95", "display_name": "Changan CS95", "vehicle_type": "7-Seat SUV", "seat_count": 7, "sort_order": 415},
    {"brand": "Changan", "model_name": "UNI-V", "display_name": "Changan UNI-V", "vehicle_type": "Fastback Sedan", "seat_count": 4, "sort_order": 416},
    {"brand": "Changan", "model_name": "UNI-K", "display_name": "Changan UNI-K", "vehicle_type": "Luxury SUV", "seat_count": 4, "sort_order": 417},
    {"brand": "Changan", "model_name": "Deepal SL03", "display_name": "Deepal SL03 EV", "vehicle_type": "Electric Sedan", "seat_count": 4, "sort_order": 418},
    {"brand": "Changan", "model_name": "Deepal S7", "display_name": "Deepal S7 EV", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 419},
    {"brand": "Changan", "model_name": "Avatr 11", "display_name": "Avatr 11 EV", "vehicle_type": "Luxury Electric SUV", "seat_count": 4, "sort_order": 420},
    {"brand": "Changan", "model_name": "Avatr 12", "display_name": "Avatr 12 EV", "vehicle_type": "Luxury Electric GT", "seat_count": 4, "sort_order": 421},

    # --- 24. GWM / HAVAL / TANK / ORA ---
    {"brand": "GWM", "model_name": "Haval H6", "display_name": "Haval H6 Hybrid", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 422},
    {"brand": "GWM", "model_name": "Haval Jolion", "display_name": "Haval Jolion Hybrid", "vehicle_type": "Compact SUV", "seat_count": 4, "sort_order": 423},
    {"brand": "GWM", "model_name": "Haval H9", "display_name": "Haval H9", "vehicle_type": "7-Seat Off-road SUV", "seat_count": 7, "sort_order": 424},
    {"brand": "Tank", "model_name": "Tank 300", "display_name": "Tank 300", "vehicle_type": "Off-road SUV", "seat_count": 4, "sort_order": 425},
    {"brand": "Tank", "model_name": "Tank 500", "display_name": "Tank 500 Hybrid", "vehicle_type": "Luxury 7-Seat SUV", "seat_count": 7, "sort_order": 426},
    {"brand": "Tank", "model_name": "Tank 700", "display_name": "Tank 700 Hi4-T", "vehicle_type": "Ultra-Luxury Off-road SUV", "seat_count": 4, "sort_order": 427},
    {"brand": "GWM", "model_name": "ORA Good Cat", "display_name": "ORA Good Cat / Funky Cat", "vehicle_type": "Electric Hatchback", "seat_count": 4, "sort_order": 428},
    {"brand": "GWM", "model_name": "ORA 07", "display_name": "ORA 07 / Lightning Cat", "vehicle_type": "Electric Fastback", "seat_count": 4, "sort_order": 429},
    {"brand": "GWM", "model_name": "Poer", "display_name": "GWM Poer Pickup", "vehicle_type": "Pickup", "seat_count": 4, "sort_order": 430},

    # --- 25. CHERY / JAECOO / OMODA ---
    {"brand": "Chery", "model_name": "Tiggo 8 Pro", "display_name": "Chery Tiggo 8 Pro Max", "vehicle_type": "7-Seat SUV", "seat_count": 7, "sort_order": 431},
    {"brand": "Chery", "model_name": "Tiggo 7 Pro", "display_name": "Chery Tiggo 7 Pro", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 432},
    {"brand": "Chery", "model_name": "Tiggo 4 Pro", "display_name": "Chery Tiggo 4 Pro", "vehicle_type": "Compact SUV", "seat_count": 4, "sort_order": 433},
    {"brand": "Chery", "model_name": "Arrizo 8", "display_name": "Chery Arrizo 8", "vehicle_type": "Executive Sedan", "seat_count": 4, "sort_order": 434},
    {"brand": "Chery", "model_name": "Arrizo 5", "display_name": "Chery Arrizo 5 Taxi", "vehicle_type": "Sedan Taxi", "seat_count": 4, "sort_order": 435},
    {"brand": "Omoda", "model_name": "Omoda 5", "display_name": "Omoda 5 / C5", "vehicle_type": "Crossover SUV", "seat_count": 4, "sort_order": 436},
    {"brand": "Omoda", "model_name": "Omoda E5", "display_name": "Omoda E5", "vehicle_type": "Electric Crossover", "seat_count": 4, "sort_order": 437},
    {"brand": "Jaecoo", "model_name": "Jaecoo 7", "display_name": "Jaecoo 7", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 438},
    {"brand": "Jaecoo", "model_name": "Jaecoo 8", "display_name": "Jaecoo 8", "vehicle_type": "Luxury 7-Seat SUV", "seat_count": 7, "sort_order": 439},

    # --- 26. GAC / AION / TRUMPCHI ---
    {"brand": "GAC", "model_name": "Aion Y Plus", "display_name": "GAC Aion Y Plus", "vehicle_type": "Electric Taxi MPV", "seat_count": 5, "sort_order": 440},
    {"brand": "GAC", "model_name": "Aion S", "display_name": "GAC Aion S Taxi", "vehicle_type": "Electric Sedan Taxi", "seat_count": 4, "sort_order": 441},
    {"brand": "GAC", "model_name": "Aion V", "display_name": "GAC Aion V", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 442},
    {"brand": "GAC", "model_name": "Trumpchi M8", "display_name": "GAC Trumpchi M8 Master", "vehicle_type": "Luxury VIP MPV", "seat_count": 7, "sort_order": 443},
    {"brand": "GAC", "model_name": "Trumpchi M6 Pro", "display_name": "GAC Trumpchi M6 Pro", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 444},
    {"brand": "GAC", "model_name": "Trumpchi GS8", "display_name": "GAC Trumpchi GS8", "vehicle_type": "7-Seat SUV", "seat_count": 7, "sort_order": 445},
    {"brand": "GAC", "model_name": "Trumpchi Empow", "display_name": "GAC Trumpchi Empow", "vehicle_type": "Sport Sedan", "seat_count": 4, "sort_order": 446},

    # --- 27. XPENG, NIO, LI AUTO, VOYAH ---
    {"brand": "XPeng", "model_name": "P7", "display_name": "XPeng P7", "vehicle_type": "Electric Sport Sedan", "seat_count": 4, "sort_order": 447},
    {"brand": "XPeng", "model_name": "G9", "display_name": "XPeng G9", "vehicle_type": "Luxury Electric SUV", "seat_count": 4, "sort_order": 448},
    {"brand": "XPeng", "model_name": "G6", "display_name": "XPeng G6", "vehicle_type": "Electric Coupe SUV", "seat_count": 4, "sort_order": 449},
    {"brand": "XPeng", "model_name": "X9", "display_name": "XPeng X9 VIP MPV", "vehicle_type": "Luxury Electric 7-Seat MPV", "seat_count": 7, "sort_order": 450},
    {"brand": "NIO", "model_name": "ET5", "display_name": "NIO ET5", "vehicle_type": "Electric Sedan", "seat_count": 4, "sort_order": 451},
    {"brand": "NIO", "model_name": "ET7", "display_name": "NIO ET7", "vehicle_type": "Luxury Electric Sedan", "seat_count": 4, "sort_order": 452},
    {"brand": "NIO", "model_name": "ES6", "display_name": "NIO ES6", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 453},
    {"brand": "NIO", "model_name": "ES8", "display_name": "NIO ES8", "vehicle_type": "Luxury 7-Seat Electric SUV", "seat_count": 7, "sort_order": 454},
    {"brand": "Li Auto", "model_name": "L7", "display_name": "Li Auto L7", "vehicle_type": "Luxury Hybrid SUV", "seat_count": 4, "sort_order": 455},
    {"brand": "Li Auto", "model_name": "L8", "display_name": "Li Auto L8", "vehicle_type": "Luxury 6-Seat Hybrid SUV", "seat_count": 6, "sort_order": 456},
    {"brand": "Li Auto", "model_name": "L9", "display_name": "Li Auto L9", "vehicle_type": "Flagship 6-Seat SUV", "seat_count": 6, "sort_order": 457},
    {"brand": "Li Auto", "model_name": "Mega", "display_name": "Li Auto Mega VIP MPV", "vehicle_type": "Ultra-Luxury Electric MPV", "seat_count": 7, "sort_order": 458},
    {"brand": "Voyah", "model_name": "Dreamer", "display_name": "Voyah Dreamer VIP MPV", "vehicle_type": "Luxury Electric MPV", "seat_count": 7, "sort_order": 459},
    {"brand": "Voyah", "model_name": "Free", "display_name": "Voyah Free", "vehicle_type": "Luxury Electric SUV", "seat_count": 4, "sort_order": 460},

    # --- 28. MAXUS / LDV & FOTON (Passenger Vans & MPVs) ---
    {"brand": "Maxus", "model_name": "G10", "display_name": "Maxus G10", "vehicle_type": "MPV", "seat_count": 9, "sort_order": 461},
    {"brand": "Maxus", "model_name": "V80", "display_name": "Maxus V80 Minibus", "vehicle_type": "Minibus", "seat_count": 15, "sort_order": 462},
    {"brand": "Maxus", "model_name": "V90", "display_name": "Maxus V90 Passenger Van", "vehicle_type": "Minibus", "seat_count": 16, "sort_order": 463},
    {"brand": "Maxus", "model_name": "G50", "display_name": "Maxus G50", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 464},
    {"brand": "Maxus", "model_name": "Mifa 9", "display_name": "Maxus Mifa 9 EV", "vehicle_type": "Electric VIP MPV", "seat_count": 7, "sort_order": 465},
    {"brand": "Maxus", "model_name": "Mifa 7", "display_name": "Maxus Mifa 7 EV", "vehicle_type": "Electric MPV", "seat_count": 7, "sort_order": 466},
    {"brand": "Maxus", "model_name": "Deliver 9", "display_name": "Maxus Deliver 9 Bus", "vehicle_type": "Minibus", "seat_count": 14, "sort_order": 467},
    {"brand": "Foton", "model_name": "View CS2", "display_name": "Foton View CS2", "vehicle_type": "Passenger Van", "seat_count": 15, "sort_order": 468},
    {"brand": "Foton", "model_name": "Toano", "display_name": "Foton Toano Minibus", "vehicle_type": "Minibus", "seat_count": 16, "sort_order": 469},
    {"brand": "Foton", "model_name": "Transvan", "display_name": "Foton Transvan", "vehicle_type": "Passenger Van", "seat_count": 13, "sort_order": 470},

    # --- 29. ISUZU, MAZDA, SUBARU, VOLVO ---
    {"brand": "Isuzu", "model_name": "MU-X", "display_name": "Isuzu MU-X", "vehicle_type": "SUV", "seat_count": 7, "sort_order": 471},
    {"brand": "Isuzu", "model_name": "D-Max", "display_name": "Isuzu D-Max", "vehicle_type": "Pickup", "seat_count": 4, "sort_order": 472},
    {"brand": "Isuzu", "model_name": "QKR Minibus", "display_name": "Isuzu QKR Minibus", "vehicle_type": "Minibus", "seat_count": 24, "sort_order": 473},
    {"brand": "Mazda", "model_name": "Mazda 3", "display_name": "Mazda 3", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 474},
    {"brand": "Mazda", "model_name": "CX-5", "display_name": "Mazda CX-5", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 475},
    {"brand": "Mazda", "model_name": "CX-8", "display_name": "Mazda CX-8", "vehicle_type": "7-Seat SUV", "seat_count": 7, "sort_order": 476},
    {"brand": "Mazda", "model_name": "CX-30", "display_name": "Mazda CX-30", "vehicle_type": "Crossover", "seat_count": 4, "sort_order": 477},
    {"brand": "Mazda", "model_name": "Mazda 2", "display_name": "Mazda 2 Sedan", "vehicle_type": "Sedan", "seat_count": 4, "sort_order": 478},
    {"brand": "Mazda", "model_name": "Mazda 6", "display_name": "Mazda 6", "vehicle_type": "Executive Sedan", "seat_count": 4, "sort_order": 479},
    {"brand": "Mazda", "model_name": "CX-60", "display_name": "Mazda CX-60", "vehicle_type": "Luxury SUV", "seat_count": 4, "sort_order": 480},
    {"brand": "Mazda", "model_name": "CX-90", "display_name": "Mazda CX-90", "vehicle_type": "Luxury 3-Row SUV", "seat_count": 8, "sort_order": 481},
    {"brand": "Mazda", "model_name": "BT-50", "display_name": "Mazda BT-50", "vehicle_type": "Pickup", "seat_count": 4, "sort_order": 482},
    {"brand": "Subaru", "model_name": "Forester", "display_name": "Subaru Forester", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 483},
    {"brand": "Subaru", "model_name": "Outback", "display_name": "Subaru Outback", "vehicle_type": "Crossover Wagon", "seat_count": 4, "sort_order": 484},
    {"brand": "Subaru", "model_name": "Crosstrek", "display_name": "Subaru Crosstrek", "vehicle_type": "Crossover", "seat_count": 4, "sort_order": 485},
    {"brand": "Volvo", "model_name": "XC90", "display_name": "Volvo XC90", "vehicle_type": "Luxury 7-Seat SUV", "seat_count": 7, "sort_order": 486},
    {"brand": "Volvo", "model_name": "XC60", "display_name": "Volvo XC60", "vehicle_type": "Luxury SUV", "seat_count": 4, "sort_order": 487},
    {"brand": "Volvo", "model_name": "S90", "display_name": "Volvo S90", "vehicle_type": "VIP Luxury Sedan", "seat_count": 4, "sort_order": 488},
    {"brand": "Volvo", "model_name": "EM90", "display_name": "Volvo EM90 VIP MPV", "vehicle_type": "Ultra-Luxury Electric MPV", "seat_count": 6, "sort_order": 489},

    # --- 30. LONDON TAXI (LEVC), VINFAST, PROTON, PERODUA, SE ASIA & REGIONAL ---
    {"brand": "LEVC", "model_name": "TX", "display_name": "LEVC TX Electric London Taxi", "vehicle_type": "Iconic London Taxi", "seat_count": 6, "sort_order": 490},
    {"brand": "LEVC", "model_name": "L380", "display_name": "LEVC L380 Multi-Seat EV", "vehicle_type": "Electric VIP MPV", "seat_count": 8, "sort_order": 491},
    {"brand": "VinFast", "model_name": "VF 5", "display_name": "VinFast VF 5 Plus Taxi", "vehicle_type": "Electric Taxi Crossover", "seat_count": 4, "sort_order": 492},
    {"brand": "VinFast", "model_name": "VF 8", "display_name": "VinFast VF 8", "vehicle_type": "Electric SUV", "seat_count": 4, "sort_order": 493},
    {"brand": "VinFast", "model_name": "VF 9", "display_name": "VinFast VF 9", "vehicle_type": "Electric 7-Seat SUV", "seat_count": 7, "sort_order": 494},
    {"brand": "VinFast", "model_name": "VF e34", "display_name": "VinFast VF e34 Taxi", "vehicle_type": "Electric Taxi Crossover", "seat_count": 4, "sort_order": 495},
    {"brand": "Proton", "model_name": "Saga", "display_name": "Proton Saga Taxi", "vehicle_type": "Sedan Taxi", "seat_count": 4, "sort_order": 496},
    {"brand": "Proton", "model_name": "Exora", "display_name": "Proton Exora", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 497},
    {"brand": "Proton", "model_name": "X70", "display_name": "Proton X70", "vehicle_type": "SUV", "seat_count": 4, "sort_order": 498},
    {"brand": "Perodua", "model_name": "Bezza", "display_name": "Perodua Bezza Taxi", "vehicle_type": "Sedan Taxi", "seat_count": 4, "sort_order": 499},
    {"brand": "Perodua", "model_name": "Alza", "display_name": "Perodua Alza", "vehicle_type": "MPV", "seat_count": 7, "sort_order": 500},
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