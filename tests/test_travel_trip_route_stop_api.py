import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime
from zoneinfo import ZoneInfo
from uuid import UUID, uuid4

import app.routes.travel as travel_routes

from app.main import app
from app.db import get_db
from app.models import AppRuntimeSetting, AuthToken, Booking, DriverWallet, Trip, User, UserNotification, Vehicle

# Monkey-patch ARRAY type for SQLite compatibility
from sqlalchemy import ARRAY as _ARRAY
from sqlalchemy.dialects.sqlite.base import SQLiteDialect as _SQLiteDialect

_orig_bp = _ARRAY.bind_processor
_orig_rp = _ARRAY.result_processor

def _patched_bp(self, dialect):
    if isinstance(dialect, _SQLiteDialect):
        def process(value):
            if value is not None:
                return json.dumps(value)
            return value
        return process
    return _orig_bp(self, dialect)

def _patched_rp(self, dialect, coltype):
    if isinstance(dialect, _SQLiteDialect):
        def process(value):
            if value is not None:
                return json.loads(value)
            return value
        return process
    return _orig_rp(self, dialect)

_ARRAY.bind_processor = _patched_bp
_ARRAY.result_processor = _patched_rp


test_engine = create_engine(
    "sqlite+pysqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


def override_get_db() -> Session:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
User.__table__.create(bind=test_engine)
AuthToken.__table__.create(bind=test_engine)
Vehicle.__table__.create(bind=test_engine)
Trip.__table__.create(bind=test_engine)
DriverWallet.__table__.create(bind=test_engine)
AppRuntimeSetting.__table__.create(bind=test_engine)

client = TestClient(app)


def _create_bookings_table() -> None:
    with test_engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TABLE bookings (
                id TEXT PRIMARY KEY,
                trip_id TEXT NOT NULL,
                passenger_id TEXT NOT NULL,
                seat_numbers TEXT NOT NULL,
                total_price NUMERIC NOT NULL,
                payment_method TEXT,
                payment_status TEXT,
                pickup_status TEXT,
                driver_arrived_at DATETIME,
                driver_requested_boarding_at DATETIME,
                passenger_confirmed_boarding_at DATETIME,
                boarding_confirmation_expires_at DATETIME,
                status TEXT,
                created_at DATETIME,
                membership_code_snapshot TEXT,
                membership_label_snapshot TEXT,
                service_fee_per_passenger_usd NUMERIC,
                service_fee_per_passenger_khr INTEGER,
                service_fee_total_usd NUMERIC,
                service_fee_total_khr INTEGER,
                fee_snapshotted_at DATETIME,
                settlement_summary_date DATE
            )
            """
        )


def _create_booking_related_tables() -> None:
    """Create payment_instruction, payments, and wallet_entries tables via SQLAlchemy ORM."""
    from app.models import BookingPaymentInstruction, Payment, DriverWalletEntry
    BookingPaymentInstruction.__table__.create(bind=test_engine, checkfirst=True)
    Payment.__table__.create(bind=test_engine, checkfirst=True)
    DriverWalletEntry.__table__.create(bind=test_engine, checkfirst=True)


def _insert_booking(booking_id: str, trip_id: str, passenger_id: str, pickup_status: str = "pending") -> None:
    """Insert a booking using hex UUIDs for SQLite ORM compatibility."""
    from uuid import UUID as _UUID
    bid = _UUID(booking_id).hex
    tid = _UUID(trip_id).hex
    pid = _UUID(passenger_id).hex
    with test_engine.begin() as connection:
        connection.exec_driver_sql(
            "INSERT INTO bookings (id, trip_id, passenger_id, seat_numbers, total_price, "
            "payment_method, payment_status, pickup_status, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (bid, tid, pid, "[1]", 5.0, "cash", "pending", pickup_status, "confirmed", "2026-06-15 11:30:00"),
        )


def _create_booking_live_locations_table() -> None:
    with test_engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TABLE booking_live_locations (
                id TEXT PRIMARY KEY,
                booking_id TEXT NOT NULL UNIQUE,
                lat NUMERIC NOT NULL,
                lng NUMERIC NOT NULL,
                accuracy_m NUMERIC,
                updated_at DATETIME NOT NULL,
                expires_at DATETIME NOT NULL
            )
            """
        )


def setup_function() -> None:
    app.dependency_overrides[get_db] = override_get_db
    with test_engine.begin() as connection:
        connection.exec_driver_sql("DROP TABLE IF EXISTS driver_wallet_entries")
        connection.exec_driver_sql("DROP TABLE IF EXISTS payments")
        connection.exec_driver_sql("DROP TABLE IF EXISTS booking_payment_instructions")
        connection.exec_driver_sql("DROP TABLE IF EXISTS booking_live_locations")
        connection.exec_driver_sql("DROP TABLE IF EXISTS bookings")
    Trip.__table__.drop(bind=test_engine, checkfirst=True)
    Vehicle.__table__.drop(bind=test_engine, checkfirst=True)
    DriverWallet.__table__.drop(bind=test_engine, checkfirst=True)
    AppRuntimeSetting.__table__.drop(bind=test_engine, checkfirst=True)
    UserNotification.__table__.drop(bind=test_engine, checkfirst=True)
    AuthToken.__table__.drop(bind=test_engine, checkfirst=True)
    User.__table__.drop(bind=test_engine, checkfirst=True)
    User.__table__.create(bind=test_engine)
    AuthToken.__table__.create(bind=test_engine)
    Vehicle.__table__.create(bind=test_engine)
    Trip.__table__.create(bind=test_engine)
    DriverWallet.__table__.create(bind=test_engine)
    AppRuntimeSetting.__table__.create(bind=test_engine)
    _create_bookings_table()
    _create_booking_live_locations_table()
    _create_booking_related_tables()
    UserNotification.__table__.create(bind=test_engine)


def _signup_driver() -> str:
    response = client.post(
        "/travel/auth/signup",
        json={
            "phone": "012345678",
            "full_name": "Driver Demo",
            "role": "driver",
            "password": "strongpass123",
            "avatar_url": None,
        },
    )
    assert response.status_code == 201
    return response.json()["token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _signup_passenger(phone: str = "098765432") -> str:
    response = client.post(
        "/travel/auth/signup",
        json={
            "phone": phone,
            "full_name": "Passenger Demo",
            "role": "passenger",
            "password": "strongpass123",
            "avatar_url": None,
        },
    )
    assert response.status_code == 201
    return response.json()["token"]


def _create_vehicle(token: str) -> str:
    response = client.post(
        "/travel/vehicles",
        headers=_auth_headers(token),
        json={
            "plate_number": "2AB-9999",
            "seat_type": 15,
            "vehicle_type": "Van",
            "model": "County",
            "color": "White",
            "company_name": "Demo Travel",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_trip_for_test(
    token: str,
    vehicle_id: str,
    *,
    departure_time: str = "2026-06-25T07:30:00",
    repeat_mode: str = "none",
) -> str:
    response = client.post(
        "/travel/trips",
        headers=_auth_headers(token),
        json={
            "vehicle_id": vehicle_id,
            "departure_province": "Kampong Thom",
            "destination_province": "Phnom Penh",
            "departure_time": departure_time,
            "departure_lat": 12.71123,
            "departure_lng": 104.88991,
            "repeat_mode": repeat_mode,
            "auto_repeat_weekly": repeat_mode == "weekly",
            "has_return_schedule": False,
            "price_per_seat": 5,
            "total_seats": 15,
            "available_seats": 15,
            "status": "scheduled",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_create_trip_with_structured_route_and_stops_round_trips_through_read_and_update() -> None:
    token = _signup_driver()
    vehicle_id = _create_vehicle(token)

    create_response = client.post(
        "/travel/trips",
        headers=_auth_headers(token),
        json={
            "vehicle_id": vehicle_id,
            "departure_province": "Kampong Thom",
            "destination_province": "Phnom Penh",
            "departure_time": "2026-06-06T07:30:00",
            "departure_lat": 12.71123,
            "departure_lng": 104.88991,
            "repeat_mode": "none",
            "auto_repeat_weekly": False,
            "has_return_schedule": False,
            "price_per_seat": 5,
            "total_seats": 15,
            "available_seats": 15,
            "status": "scheduled",
            "departure_route": {
                "province_code": "06",
                "province_name": "កំពង់ធំ",
                "district_code": "0601",
                "district_name": "ស្ទឹងសែន",
                "commune_code": "060101",
                "commune_name": "ស្ទឹងសែន",
            },
            "destination_route": {
                "province_code": "12",
                "province_name": "ភ្នំពេញ",
                "district_code": "1201",
                "district_name": "ដូនពេញ",
                "commune_code": "120101",
                "commune_name": "ផ្សារកណ្ដាល",
            },
            "pickup_stop": {
                "id": 101,
                "source": "catalog",
                "label": "ផ្សារកំពង់ធំ",
                "landmark_note": "ច្រកខាងមុខផ្សារ",
                "latitude": 12.71123,
                "longitude": 104.88991,
                "commune_code": "060101",
                "commune_name": "ស្ទឹងសែន",
                "district_code": "0601",
                "district_name": "ស្ទឹងសែន",
                "province_code": "06",
                "province_name": "កំពង់ធំ",
            },
            "dropoff_stop": {
                "source": "manual_pin",
                "label": "មុខរបងវត្ត",
                "landmark_note": "មុខរបងវត្ត",
                "latitude": 11.57321,
                "longitude": 104.92111,
                "commune_code": "120101",
                "commune_name": "ផ្សារកណ្ដាល",
                "district_code": "1201",
                "district_name": "ដូនពេញ",
                "province_code": "12",
                "province_name": "ភ្នំពេញ",
            },
        },
    )

    assert create_response.status_code == 201
    created_trip = create_response.json()
    assert created_trip["departure_route"]["commune_code"] == "060101"
    assert created_trip["destination_route"]["commune_code"] == "120101"
    assert created_trip["pickup_stop"]["source"] == "catalog"
    assert created_trip["dropoff_stop"]["source"] == "manual_pin"

    trip_id = created_trip["id"]
    update_response = client.patch(
        f"/travel/trips/{trip_id}",
        headers=_auth_headers(token),
        json={"price_per_seat": 6},
    )

    assert update_response.status_code == 200
    updated_trip = update_response.json()
    assert updated_trip["price_per_seat"] == 6.0
    assert updated_trip["departure_route"]["commune_code"] == "060101"
    assert updated_trip["pickup_stop"]["label"] == "ផ្សារកំពង់ធំ"
    assert updated_trip["dropoff_stop"]["label"] == "មុខរបងវត្ត"

    get_response = client.get(f"/travel/trips/{trip_id}")

    assert get_response.status_code == 200
    fetched_trip = get_response.json()
    assert fetched_trip["departure_route"]["province_code"] == "06"
    assert fetched_trip["destination_route"]["province_code"] == "12"
    assert fetched_trip["pickup_stop"]["id"] == 101
    assert fetched_trip["dropoff_stop"]["source"] == "manual_pin"


def test_create_trip_rejects_stop_commune_mismatch() -> None:
    token = _signup_driver()
    vehicle_id = _create_vehicle(token)

    response = client.post(
        "/travel/trips",
        headers=_auth_headers(token),
        json={
            "vehicle_id": vehicle_id,
            "departure_province": "Kampong Thom",
            "destination_province": "Phnom Penh",
            "departure_time": "2026-06-06T07:30:00",
            "price_per_seat": 5,
            "total_seats": 15,
            "available_seats": 15,
            "status": "scheduled",
            "departure_route": {
                "province_code": "06",
                "province_name": "កំពង់ធំ",
                "district_code": "0601",
                "district_name": "ស្ទឹងសែន",
                "commune_code": "060101",
                "commune_name": "ស្ទឹងសែន",
            },
            "pickup_stop": {
                "source": "catalog",
                "label": "ផ្សារកំពង់ធំ",
                "latitude": 12.71123,
                "longitude": 104.88991,
                "commune_code": "999999",
                "commune_name": "Wrong Commune",
            },
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "pickup_stop.commune_code must match departure_route.commune_code"


def test_search_trips_includes_active_and_scheduled_results_in_real_time_for_same_local_day(
    monkeypatch,
) -> None:
    frozen_now = datetime(2026, 6, 15, 10, 0, 0)
    tz = ZoneInfo("Asia/Phnom_Penh")
    monkeypatch.setattr(travel_routes, "phnom_penh_now", lambda: frozen_now)
    monkeypatch.setattr(travel_routes, "_local_now", lambda _: frozen_now)

    token = _signup_driver()
    vehicle_id = _create_vehicle(token)

    active_response = client.post(
        "/travel/trips",
        headers=_auth_headers(token),
        json={
            "vehicle_id": vehicle_id,
            "departure_province": "ភ្នំពេញ",
            "destination_province": "កណ្ដាល",
            "departure_time": "2026-06-15T08:30:00",
            "departure_lat": 11.5564,
            "departure_lng": 104.9282,
            "price_per_seat": 5,
            "total_seats": 15,
            "available_seats": 12,
            "status": "active",
        },
    )
    assert active_response.status_code == 201
    active_trip_id = active_response.json()["id"]

    scheduled_response = client.post(
        "/travel/trips",
        headers=_auth_headers(token),
        json={
            "vehicle_id": vehicle_id,
            "departure_province": "ភ្នំពេញ",
            "destination_province": "កណ្ដាល",
            "departure_time": "2026-06-15T13:30:00",
            "price_per_seat": 5,
            "total_seats": 15,
            "available_seats": 15,
            "status": "scheduled",
        },
    )
    assert scheduled_response.status_code == 201
    scheduled_trip_id = scheduled_response.json()["id"]

    search_response = client.get(
        "/travel/trips/search",
        params={
            "departure_province": "ភ្នំពេញ",
            "destination_province": "កណ្ដាល",
            "journey_date": "2026-06-15",
            "timezone": tz.key,
        },
    )
    assert search_response.status_code == 200
    search_ids = {trip["id"] for trip in search_response.json()}
    assert active_trip_id in search_ids
    assert scheduled_trip_id in search_ids

    default_timezone_response = client.get(
        "/travel/trips/search",
        params={
            "departure_province": "ភ្នំពេញ",
            "destination_province": "កណ្ដាល",
            "journey_date": "2026-06-15",
        },
    )
    assert default_timezone_response.status_code == 200
    default_timezone_ids = {
        trip["id"] for trip in default_timezone_response.json()
    }
    assert active_trip_id in default_timezone_ids
    assert scheduled_trip_id in default_timezone_ids

    now_response = client.get(
        "/travel/trips/search",
        params={
            "departure_province": "ភ្នំពេញ",
            "destination_province": "កណ្ដាល",
            "journey_date": "2026-06-15",
            "schedule": "now",
            "timezone": tz.key,
        },
    )
    assert now_response.status_code == 200
    now_ids = {trip["id"] for trip in now_response.json()}
    assert active_trip_id in now_ids
    assert scheduled_trip_id in now_ids


def test_complete_trip_rejects_completion_before_departure_time(monkeypatch) -> None:
    frozen_now = datetime(2026, 6, 15, 11, 19, 0)
    monkeypatch.setattr(travel_routes, "phnom_penh_now", lambda: frozen_now)

    token = _signup_driver()
    vehicle_id = _create_vehicle(token)

    create_response = client.post(
        "/travel/trips",
        headers=_auth_headers(token),
        json={
            "vehicle_id": vehicle_id,
            "departure_province": "ភ្នំពេញ",
            "destination_province": "កណ្ដាល",
            "departure_time": "2026-06-15T11:30:00",
            "price_per_seat": 5,
            "total_seats": 4,
            "available_seats": 4,
            "status": "scheduled",
        },
    )
    assert create_response.status_code == 201
    trip_id = create_response.json()["id"]

    complete_response = client.post(
        f"/travel/trips/{trip_id}/complete",
        headers=_auth_headers(token),
    )

    assert complete_response.status_code == 400
    assert (
        complete_response.json()["detail"]
        == "Trip cannot be completed before its departure time"
    )

    get_response = client.get(f"/travel/trips/{trip_id}")
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "scheduled"


def test_search_trips_repairs_future_trip_marked_completed_too_early(monkeypatch) -> None:
    frozen_now = datetime(2026, 6, 15, 11, 19, 0)
    tz = ZoneInfo("Asia/Phnom_Penh")
    monkeypatch.setattr(travel_routes, "phnom_penh_now", lambda: frozen_now)
    monkeypatch.setattr(travel_routes, "_local_now", lambda _: frozen_now)

    token = _signup_driver()
    vehicle_id = _create_vehicle(token)

    create_response = client.post(
        "/travel/trips",
        headers=_auth_headers(token),
        json={
            "vehicle_id": vehicle_id,
            "departure_province": "Phnom Penh Capital",
            "destination_province": "Kandal Province",
            "departure_time": "2026-06-15T11:30:00",
            "price_per_seat": 5,
            "total_seats": 4,
            "available_seats": 4,
            "status": "scheduled",
        },
    )
    assert create_response.status_code == 201
    trip_id = create_response.json()["id"]

    with TestingSessionLocal() as db:
        trip = db.get(Trip, UUID(trip_id))
        assert trip is not None
        trip.status = "completed"
        db.commit()

    search_response = client.get(
        "/travel/trips/search",
        params={
            "departure_province": "ភ្នំពេញ",
            "destination_province": "កណ្ដាល",
            "journey_date": "2026-06-15",
            "timezone": tz.key,
        },
    )
    assert search_response.status_code == 200
    search_ids = {trip["id"] for trip in search_response.json()}
    assert trip_id in search_ids

    get_response = client.get(f"/travel/trips/{trip_id}")
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "scheduled"


def test_create_booking_creates_driver_notification() -> None:
    driver_token = _signup_driver()
    passenger_token = _signup_passenger()
    vehicle_id = _create_vehicle(driver_token)

    trip_response = client.post(
        "/travel/trips",
        headers=_auth_headers(driver_token),
        json={
            "vehicle_id": vehicle_id,
            "departure_province": "Phnom Penh",
            "destination_province": "Kandal",
            "departure_time": "2026-06-15T11:30:00",
            "price_per_seat": 5,
            "total_seats": 4,
            "available_seats": 4,
            "status": "scheduled",
        },
    )
    assert trip_response.status_code == 201
    trip_id = trip_response.json()["id"]

    with TestingSessionLocal() as db:
        trip = db.get(Trip, UUID(trip_id))
        passenger = db.execute(
            select(User).where(User.role == "passenger")
        ).scalar_one()
        assert trip is not None
        booking = travel_routes.Booking(
            id=uuid4(),
            trip_id=trip.id,
            passenger_id=passenger.id,
            seat_numbers=[1, 2],
            total_price=10,
            payment_method="cash",
            payment_status="pending",
            pickup_status="pending",
            status="confirmed",
        )
        travel_routes._create_driver_booking_notification(db, trip, booking, passenger)
        db.commit()
        booking_id = str(booking.id)

    notifications_response = client.get(
        "/travel/notifications",
        headers=_auth_headers(driver_token),
    )
    assert notifications_response.status_code == 200
    payload = notifications_response.json()
    assert payload["unread_count"] == 1
    assert payload["notifications"][0]["type"] == "booking_created"
    assert payload["notifications"][0]["booking_id"] == booking_id
    assert "Passenger Demo booked 2 seats" in payload["notifications"][0]["body"]


def test_mark_driver_arrived_creates_passenger_notification() -> None:
    driver_token = _signup_driver()
    passenger_token = _signup_passenger()
    vehicle_id = _create_vehicle(driver_token)

    trip_response = client.post(
        "/travel/trips",
        headers=_auth_headers(driver_token),
        json={
            "vehicle_id": vehicle_id,
            "departure_province": "Phnom Penh",
            "destination_province": "Kandal",
            "departure_time": "2026-06-15T11:30:00",
            "price_per_seat": 5,
            "total_seats": 4,
            "available_seats": 4,
            "status": "scheduled",
        },
    )
    assert trip_response.status_code == 201
    trip_id = trip_response.json()["id"]

    with TestingSessionLocal() as db:
        trip = db.get(Trip, UUID(trip_id))
        passenger = db.execute(
            select(User).where(User.role == "passenger")
        ).scalar_one()
        assert trip is not None
        booking = travel_routes.Booking(
            id=uuid4(),
            trip_id=trip.id,
            passenger_id=passenger.id,
            seat_numbers=[1],
            total_price=5,
            payment_method="cash",
            payment_status="pending",
            pickup_status="driver_arrived",
            status="confirmed",
        )
        travel_routes._create_driver_arrived_notification(db, booking)
        db.commit()
        booking_id = str(booking.id)

    notifications_response = client.get(
        "/travel/notifications",
        headers=_auth_headers(passenger_token),
    )
    assert notifications_response.status_code == 200
    payload = notifications_response.json()
    assert payload["unread_count"] == 1
    assert payload["notifications"][0]["type"] == "driver_arrived"
    assert payload["notifications"][0]["booking_id"] == booking_id


def test_driver_arrived_fails_without_live_location() -> None:
    driver_token = _signup_driver()
    _signup_passenger()
    vehicle_id = _create_vehicle(driver_token)

    trip_response = client.post(
        "/travel/trips",
        headers=_auth_headers(driver_token),
        json={
            "vehicle_id": vehicle_id,
            "departure_province": "Phnom Penh",
            "destination_province": "Kandal",
            "departure_time": "2099-06-15T11:30:00",
            "price_per_seat": 5,
            "total_seats": 4,
            "available_seats": 4,
            "status": "scheduled",
        },
    )
    assert trip_response.status_code == 201
    trip_id = trip_response.json()["id"]

    with TestingSessionLocal() as db:
        passenger = db.execute(select(User).where(User.role == "passenger")).scalar_one()
        booking_id = str(uuid4())
        _insert_booking(booking_id, trip_id, str(passenger.id))

    response = client.post(
        f"/travel/bookings/{booking_id}/driver-arrived",
        headers=_auth_headers(driver_token),
    )
    assert response.status_code == 400
    assert "location is not available" in response.json()["detail"].lower()


def test_driver_arrived_succeeds_with_live_location(monkeypatch) -> None:
    frozen_now = datetime(2026, 6, 15, 11, 30, 0)
    monkeypatch.setattr(travel_routes, "phnom_penh_now", lambda: frozen_now)

    driver_token = _signup_driver()
    passenger_token = _signup_passenger()
    vehicle_id = _create_vehicle(driver_token)

    trip_response = client.post(
        "/travel/trips",
        headers=_auth_headers(driver_token),
        json={
            "vehicle_id": vehicle_id,
            "departure_province": "Phnom Penh",
            "destination_province": "Kandal",
            "departure_time": "2026-06-15T11:30:00",
            "departure_lat": 11.5564,
            "departure_lng": 104.9282,
            "price_per_seat": 5,
            "total_seats": 4,
            "available_seats": 4,
            "status": "scheduled",
        },
    )
    assert trip_response.status_code == 201
    trip_id = trip_response.json()["id"]

    with TestingSessionLocal() as db:
        passenger = db.execute(select(User).where(User.role == "passenger")).scalar_one()
        booking_id = str(uuid4())
        _insert_booking(booking_id, trip_id, str(passenger.id))

    # Passenger shares live location close to driver
    loc_resp = client.put(
        f"/travel/bookings/{booking_id}/passenger-live-location",
        headers=_auth_headers(passenger_token),
        json={"lat": 11.5565, "lng": 104.9283, "accuracy_m": 10},
    )
    assert loc_resp.status_code == 200

    response = client.post(
        f"/travel/bookings/{booking_id}/driver-arrived",
        headers=_auth_headers(driver_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pickup_status"] == "driver_arrived"
    assert data["driver_arrived_at"] is not None


def test_driver_arrived_uses_pickup_point_when_passenger_location_missing(monkeypatch) -> None:
    frozen_now = datetime(2026, 6, 15, 11, 30, 0)
    monkeypatch.setattr(travel_routes, "phnom_penh_now", lambda: frozen_now)

    driver_token = _signup_driver()
    _signup_passenger()
    vehicle_id = _create_vehicle(driver_token)

    trip_response = client.post(
        "/travel/trips",
        headers=_auth_headers(driver_token),
        json={
            "vehicle_id": vehicle_id,
            "departure_province": "Phnom Penh",
            "destination_province": "Kandal",
            "departure_time": "2026-06-15T11:30:00",
            "departure_lat": 11.5564,
            "departure_lng": 104.9282,
            "price_per_seat": 5,
            "total_seats": 4,
            "available_seats": 4,
            "status": "scheduled",
        },
    )
    assert trip_response.status_code == 201
    trip_id = trip_response.json()["id"]

    with TestingSessionLocal() as db:
        passenger = db.execute(select(User).where(User.role == "passenger")).scalar_one()
        booking_id = str(uuid4())
        _insert_booking(booking_id, trip_id, str(passenger.id))

    # No passenger live location set. Driver is already at the pickup point.
    response = client.post(
        f"/travel/bookings/{booking_id}/driver-arrived",
        headers=_auth_headers(driver_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pickup_status"] == "driver_arrived"
    assert data["driver_arrived_at"] is not None


def test_driver_arrived_fails_when_passenger_too_far(monkeypatch) -> None:
    frozen_now = datetime(2026, 6, 15, 11, 30, 0)
    monkeypatch.setattr(travel_routes, "phnom_penh_now", lambda: frozen_now)

    driver_token = _signup_driver()
    passenger_token = _signup_passenger("098765435")
    vehicle_id = _create_vehicle(driver_token)

    trip_response = client.post(
        "/travel/trips",
        headers=_auth_headers(driver_token),
        json={
            "vehicle_id": vehicle_id,
            "departure_province": "Phnom Penh",
            "destination_province": "Kandal",
            "departure_time": "2026-06-15T11:30:00",
            "departure_lat": 11.5564,
            "departure_lng": 104.9282,
            "price_per_seat": 5,
            "total_seats": 4,
            "available_seats": 4,
            "status": "scheduled",
        },
    )
    assert trip_response.status_code == 201
    trip_id = trip_response.json()["id"]

    with TestingSessionLocal() as db:
        passenger = db.execute(
            select(User).where(User.phone == "098765435")
        ).scalar_one()
        booking_id = str(uuid4())
        _insert_booking(booking_id, trip_id, str(passenger.id))

    # Passenger shares location ~1km away
    loc_resp = client.put(
        f"/travel/bookings/{booking_id}/passenger-live-location",
        headers=_auth_headers(passenger_token),
        json={"lat": 11.5650, "lng": 104.9350, "accuracy_m": 10},
    )
    assert loc_resp.status_code == 200

    response = client.post(
        f"/travel/bookings/{booking_id}/driver-arrived",
        headers=_auth_headers(driver_token),
    )
    assert response.status_code == 400
    detail = response.json()["detail"].lower()
    assert "move within 100m" in detail
    assert "m from the passenger" in detail


def test_driver_arrived_uses_pickup_point_when_passenger_location_stale(monkeypatch) -> None:
    """Stale passenger live location falls back to the booking pickup point."""
    base_time = datetime(2026, 6, 15, 11, 30, 0)
    monkeypatch.setattr(travel_routes, "phnom_penh_now", lambda: base_time)

    driver_token = _signup_driver()
    passenger_token = _signup_passenger("098765436")
    vehicle_id = _create_vehicle(driver_token)

    trip_response = client.post(
        "/travel/trips",
        headers=_auth_headers(driver_token),
        json={
            "vehicle_id": vehicle_id,
            "departure_province": "Phnom Penh",
            "destination_province": "Kandal",
            "departure_time": "2026-06-15T11:30:00",
            "departure_lat": 11.5564,
            "departure_lng": 104.9282,
            "price_per_seat": 5,
            "total_seats": 4,
            "available_seats": 4,
            "status": "scheduled",
        },
    )
    assert trip_response.status_code == 201
    trip_id = trip_response.json()["id"]

    with TestingSessionLocal() as db:
        passenger = db.execute(
            select(User).where(User.phone == "098765436")
        ).scalar_one()
        booking_id = str(uuid4())
        _insert_booking(booking_id, trip_id, str(passenger.id))

    # Passenger shares location
    loc_resp = client.put(
        f"/travel/bookings/{booking_id}/passenger-live-location",
        headers=_auth_headers(passenger_token),
        json={"lat": 11.5565, "lng": 104.9283, "accuracy_m": 10},
    )
    assert loc_resp.status_code == 200

    # Advance time past the 60s TTL
    stale_time = datetime(2026, 6, 15, 11, 32, 0)  # 90s later
    monkeypatch.setattr(travel_routes, "phnom_penh_now", lambda: stale_time)

    response = client.post(
        f"/travel/bookings/{booking_id}/driver-arrived",
        headers=_auth_headers(driver_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pickup_status"] == "driver_arrived"
    assert data["driver_arrived_at"] is not None


def test_boarding_request_requires_driver_arrived_first(monkeypatch) -> None:
    frozen_now = datetime(2026, 6, 15, 11, 30, 0)
    monkeypatch.setattr(travel_routes, "phnom_penh_now", lambda: frozen_now)

    driver_token = _signup_driver()
    _signup_passenger()
    vehicle_id = _create_vehicle(driver_token)

    trip_response = client.post(
        "/travel/trips",
        headers=_auth_headers(driver_token),
        json={
            "vehicle_id": vehicle_id,
            "departure_province": "Phnom Penh",
            "destination_province": "Kandal",
            "departure_time": "2026-06-15T11:30:00",
            "departure_lat": 11.5564,
            "departure_lng": 104.9282,
            "price_per_seat": 5,
            "total_seats": 4,
            "available_seats": 4,
            "status": "scheduled",
        },
    )
    assert trip_response.status_code == 201
    trip_id = trip_response.json()["id"]

    with TestingSessionLocal() as db:
        passenger = db.execute(select(User).where(User.role == "passenger")).scalar_one()
        booking_id = str(uuid4())
        _insert_booking(booking_id, trip_id, str(passenger.id))

    response = client.post(
        f"/travel/bookings/{booking_id}/boarding/request",
        headers=_auth_headers(driver_token),
    )
    assert response.status_code == 400
    assert "mark arrival" in response.json()["detail"].lower()


def test_full_boarding_flow(monkeypatch) -> None:
    frozen_now = datetime(2026, 6, 15, 11, 30, 0)
    monkeypatch.setattr(travel_routes, "phnom_penh_now", lambda: frozen_now)

    driver_token = _signup_driver()
    passenger_token = _signup_passenger("098765433")
    vehicle_id = _create_vehicle(driver_token)

    trip_response = client.post(
        "/travel/trips",
        headers=_auth_headers(driver_token),
        json={
            "vehicle_id": vehicle_id,
            "departure_province": "Phnom Penh",
            "destination_province": "Kandal",
            "departure_time": "2026-06-15T11:30:00",
            "departure_lat": 11.5564,
            "departure_lng": 104.9282,
            "price_per_seat": 5,
            "total_seats": 4,
            "available_seats": 4,
            "status": "scheduled",
        },
    )
    assert trip_response.status_code == 201
    trip_id = trip_response.json()["id"]

    with TestingSessionLocal() as db:
        passenger = db.execute(
            select(User).where(User.phone == "098765433")
        ).scalar_one()
        booking_id = str(uuid4())
        _insert_booking(booking_id, trip_id, str(passenger.id))

    # Passenger shares live location close to driver
    loc_resp = client.put(
        f"/travel/bookings/{booking_id}/passenger-live-location",
        headers=_auth_headers(passenger_token),
        json={"lat": 11.5565, "lng": 104.9283, "accuracy_m": 10},
    )
    assert loc_resp.status_code == 200

    # Step 1: Driver arrives (has departure_lat/lng = live location)
    arrived = client.post(
        f"/travel/bookings/{booking_id}/driver-arrived",
        headers=_auth_headers(driver_token),
    )
    assert arrived.status_code == 200

    # Step 2: Driver requests boarding
    request_resp = client.post(
        f"/travel/bookings/{booking_id}/boarding/request",
        headers=_auth_headers(driver_token),
    )
    assert request_resp.status_code == 200
    assert request_resp.json()["driver_requested_boarding_at"] is not None

    # Step 3: Check boarding status from passenger side
    status_resp = client.get(
        f"/travel/bookings/{booking_id}/boarding/status",
        headers=_auth_headers(passenger_token),
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "requested"

    # Step 4: Passenger confirms boarding
    confirm_resp = client.post(
        f"/travel/bookings/{booking_id}/boarding/passenger-confirm",
        headers=_auth_headers(passenger_token),
    )
    assert confirm_resp.status_code == 200
    data = confirm_resp.json()
    assert data["pickup_status"] == "passenger_boarded"
    assert data["status"] == "confirmed"
    assert data["passenger_confirmed_boarding_at"] is not None

    # Step 5: Check notification was created for driver
    notifications = client.get(
        "/travel/notifications",
        headers=_auth_headers(driver_token),
    )
    assert notifications.status_code == 200
    types = [n["type"] for n in notifications.json()["notifications"]]
    assert "boarding_confirmed" in types


def test_boarding_cancel(monkeypatch) -> None:
    frozen_now = datetime(2026, 6, 15, 11, 30, 0)
    monkeypatch.setattr(travel_routes, "phnom_penh_now", lambda: frozen_now)

    driver_token = _signup_driver()
    passenger_token = _signup_passenger("098765434")
    vehicle_id = _create_vehicle(driver_token)

    trip_response = client.post(
        "/travel/trips",
        headers=_auth_headers(driver_token),
        json={
            "vehicle_id": vehicle_id,
            "departure_province": "Phnom Penh",
            "destination_province": "Kandal",
            "departure_time": "2026-06-15T11:30:00",
            "departure_lat": 11.5564,
            "departure_lng": 104.9282,
            "price_per_seat": 5,
            "total_seats": 4,
            "available_seats": 4,
            "status": "scheduled",
        },
    )
    assert trip_response.status_code == 201
    trip_id = trip_response.json()["id"]

    with TestingSessionLocal() as db:
        passenger = db.execute(
            select(User).where(User.phone == "098765434")
        ).scalar_one()
        booking_id = str(uuid4())
        _insert_booking(booking_id, trip_id, str(passenger.id))

    # Passenger shares live location close to driver
    loc_resp = client.put(
        f"/travel/bookings/{booking_id}/passenger-live-location",
        headers=_auth_headers(passenger_token),
        json={"lat": 11.5565, "lng": 104.9283, "accuracy_m": 10},
    )
    assert loc_resp.status_code == 200

    # Mark arrived
    arrived_resp = client.post(
        f"/travel/bookings/{booking_id}/driver-arrived",
        headers=_auth_headers(driver_token),
    )
    assert arrived_resp.status_code == 200

    # Request boarding
    request_resp = client.post(
        f"/travel/bookings/{booking_id}/boarding/request",
        headers=_auth_headers(driver_token),
    )
    assert request_resp.status_code == 200

    # Passenger declines/cancels boarding so the driver can call or retry.
    cancel_resp = client.post(
        f"/travel/bookings/{booking_id}/boarding/cancel",
        headers=_auth_headers(passenger_token),
    )
    assert cancel_resp.status_code == 200
    data = cancel_resp.json()
    assert data["driver_requested_boarding_at"] is None
    assert data["boarding_confirmation_expires_at"] is None

    status_resp = client.get(
        f"/travel/bookings/{booking_id}/boarding/status",
        headers=_auth_headers(driver_token),
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "none"


def test_booking_passenger_contact_scoped_to_booking_users(monkeypatch) -> None:
    frozen_now = datetime(2026, 6, 15, 11, 30, 0)
    monkeypatch.setattr(travel_routes, "phnom_penh_now", lambda: frozen_now)

    driver_token = _signup_driver()
    passenger_token = _signup_passenger("098765436")
    other_passenger_token = _signup_passenger("098765437")
    vehicle_id = _create_vehicle(driver_token)

    trip_response = client.post(
        "/travel/trips",
        headers=_auth_headers(driver_token),
        json={
            "vehicle_id": vehicle_id,
            "departure_province": "Phnom Penh",
            "destination_province": "Kandal",
            "departure_time": "2026-06-15T11:30:00",
            "departure_lat": 11.5564,
            "departure_lng": 104.9282,
            "price_per_seat": 5,
            "total_seats": 4,
            "available_seats": 4,
            "status": "scheduled",
        },
    )
    assert trip_response.status_code == 201
    trip_id = trip_response.json()["id"]

    with TestingSessionLocal() as db:
        passenger = db.execute(
            select(User).where(User.phone == "098765436")
        ).scalar_one()
        booking_id = str(uuid4())
        _insert_booking(booking_id, trip_id, str(passenger.id))

    live_location_resp = client.put(
        f"/travel/bookings/{booking_id}/passenger-live-location",
        headers=_auth_headers(passenger_token),
        json={"lat": 11.5565, "lng": 104.9283, "accuracy_m": 8},
    )
    assert live_location_resp.status_code == 200

    driver_bookings = client.get(
        "/travel/bookings",
        headers=_auth_headers(driver_token),
    )
    assert driver_bookings.status_code == 200
    driver_booking = next(
        item for item in driver_bookings.json() if item["id"] == booking_id
    )
    assert driver_booking["passenger_contact"]["phone"] == "098765436"
    assert driver_booking["passenger_live_location"]["lat"] == 11.5565
    assert driver_booking["passenger_live_location"]["lng"] == 104.9283
    assert driver_booking["passenger_live_location"]["accuracy_m"] == 8

    passenger_booking = client.get(
        f"/travel/bookings/{booking_id}",
        headers=_auth_headers(passenger_token),
    )
    assert passenger_booking.status_code == 200
    assert passenger_booking.json()["passenger_contact"]["phone"] == "098765436"
    assert passenger_booking.json()["passenger_live_location"]["lat"] == 11.5565
    assert passenger_booking.json()["passenger_live_location"]["lng"] == 104.9283

    denied = client.get(
        f"/travel/bookings/{booking_id}",
        headers=_auth_headers(other_passenger_token),
    )
    assert denied.status_code == 403


def test_passenger_live_location(monkeypatch) -> None:
    frozen_now = datetime(2026, 6, 15, 11, 30, 0)
    monkeypatch.setattr(travel_routes, "phnom_penh_now", lambda: frozen_now)

    driver_token = _signup_driver()
    passenger_token = _signup_passenger("098765435")
    vehicle_id = _create_vehicle(driver_token)

    trip_response = client.post(
        "/travel/trips",
        headers=_auth_headers(driver_token),
        json={
            "vehicle_id": vehicle_id,
            "departure_province": "Phnom Penh",
            "destination_province": "Kandal",
            "departure_time": "2026-06-15T11:30:00",
            "departure_lat": 11.5564,
            "departure_lng": 104.9282,
            "price_per_seat": 5,
            "total_seats": 4,
            "available_seats": 4,
            "status": "scheduled",
        },
    )
    assert trip_response.status_code == 201
    trip_id = trip_response.json()["id"]

    with TestingSessionLocal() as db:
        passenger = db.execute(
            select(User).where(User.phone == "098765435")
        ).scalar_one()
        booking_id = str(uuid4())
        _insert_booking(booking_id, trip_id, str(passenger.id))

    # Update passenger live location
    loc_resp = client.put(
        f"/travel/bookings/{booking_id}/passenger-live-location",
        headers=_auth_headers(passenger_token),
        json={"lat": 11.5565, "lng": 104.9283, "accuracy_m": 10},
    )
    assert loc_resp.status_code == 200
    assert loc_resp.json()["status"] == "ok"

    # Driver checks proximity
    prox_resp = client.get(
        f"/travel/bookings/{booking_id}/proximity",
        headers=_auth_headers(driver_token),
    )
    assert prox_resp.status_code == 200
    prox = prox_resp.json()
    assert prox["driver_location_fresh"] is True
    assert prox["passenger_location_fresh"] is True
    assert prox["distance_m"] > 0
    assert prox["within_threshold"] is True


def test_expired_trip_cancels_active_bookings_and_clears_passenger_active_state(monkeypatch) -> None:
    frozen_now = datetime(2026, 6, 20, 12, 0, 0)
    monkeypatch.setattr(travel_routes, "phnom_penh_now", lambda: frozen_now)

    driver_token = _signup_driver()
    passenger_token = _signup_passenger()
    vehicle_id = _create_vehicle(driver_token)
    trip_id = _create_trip_for_test(driver_token, vehicle_id)

    with TestingSessionLocal() as db:
        passenger = db.execute(
            select(User).where(User.role == "passenger")
        ).scalar_one()
        booking_id = str(uuid4())
        _insert_booking(booking_id, trip_id, str(passenger.id))

    with TestingSessionLocal() as db:
        trip = db.get(Trip, UUID(trip_id))
        assert trip is not None
        trip.departure_time = datetime(2026, 6, 15, 7, 30, 0)
        trip.live_location_expires_at = datetime(2026, 6, 16, 7, 30, 0)
        db.commit()

    driver_bookings = client.get(
        "/travel/bookings",
        headers=_auth_headers(driver_token),
    )
    assert driver_bookings.status_code == 200
    expired_booking = next(item for item in driver_bookings.json() if item["id"] == booking_id)
    assert expired_booking["status"] == "cancelled"
    assert expired_booking["trip"]["status"] == "cancelled"

    passenger_active = client.get(
        "/travel/bookings/active",
        headers=_auth_headers(passenger_token),
    )
    assert passenger_active.status_code == 200
    assert passenger_active.json()["booking"] is None


def test_expired_daily_trip_creates_next_scheduled_repeat(monkeypatch) -> None:
    frozen_now = datetime(2026, 6, 20, 12, 0, 0)
    monkeypatch.setattr(travel_routes, "phnom_penh_now", lambda: frozen_now)

    driver_token = _signup_driver()
    vehicle_id = _create_vehicle(driver_token)
    trip_id = _create_trip_for_test(driver_token, vehicle_id, repeat_mode="daily")

    with TestingSessionLocal() as db:
        trip = db.get(Trip, UUID(trip_id))
        assert trip is not None
        trip.departure_time = datetime(2026, 6, 15, 7, 30, 0)
        trip.live_location_expires_at = datetime(2026, 6, 16, 7, 30, 0)
        trip.recurring_departure_time = datetime(2026, 6, 15, 7, 30, 0).time()
        db.commit()

    trips_response = client.get(
        "/travel/driver/trips",
        headers=_auth_headers(driver_token),
    )
    assert trips_response.status_code == 200

    trips = trips_response.json()
    cancelled_original = next(item for item in trips if item["id"] == trip_id)
    repeated_trip = next(
        item
        for item in trips
        if item["id"] != trip_id and item["status"] == "scheduled"
    )
    assert cancelled_original["status"] == "cancelled"
    assert repeated_trip["repeat_mode"] == "daily"
    assert repeated_trip["departure_time"].startswith("2026-06-20T07:30:00")
