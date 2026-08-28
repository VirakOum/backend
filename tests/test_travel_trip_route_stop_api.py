import asyncio
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, selectinload, sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime
from zoneinfo import ZoneInfo
from uuid import UUID, uuid4

import app.routes.travel as travel_routes
import app.routes.live_ws as live_ws_routes

from app.main import app
from app.db import get_db
from app.models import AppRuntimeSetting, AuthToken, Booking, DriverMembership, DriverWallet, DriverWalletEntry, Trip, TrustedDevice, User, UserNotification, Vehicle

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
TrustedDevice.__table__.create(bind=test_engine)
Vehicle.__table__.create(bind=test_engine)
Trip.__table__.create(bind=test_engine)
DriverWallet.__table__.create(bind=test_engine)
DriverMembership.__table__.create(bind=test_engine)
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
                currency TEXT DEFAULT 'KHR',
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


def _insert_booking(
    booking_id: str,
    trip_id: str,
    passenger_id: str,
    pickup_status: str = "pending",
    *,
    total_price: float = 5.0,
) -> None:
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
            (bid, tid, pid, "[1]", total_price, "cash", "pending", pickup_status, "confirmed", "2026-06-15 11:30:00"),
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
    DriverMembership.__table__.drop(bind=test_engine, checkfirst=True)
    DriverWallet.__table__.drop(bind=test_engine, checkfirst=True)
    AppRuntimeSetting.__table__.drop(bind=test_engine, checkfirst=True)
    UserNotification.__table__.drop(bind=test_engine, checkfirst=True)
    TrustedDevice.__table__.drop(bind=test_engine, checkfirst=True)
    AuthToken.__table__.drop(bind=test_engine, checkfirst=True)
    User.__table__.drop(bind=test_engine, checkfirst=True)
    User.__table__.create(bind=test_engine)
    AuthToken.__table__.create(bind=test_engine)
    TrustedDevice.__table__.create(bind=test_engine)
    Vehicle.__table__.create(bind=test_engine)
    Trip.__table__.create(bind=test_engine)
    DriverWallet.__table__.create(bind=test_engine)
    DriverMembership.__table__.create(bind=test_engine)
    AppRuntimeSetting.__table__.create(bind=test_engine)
    _create_bookings_table()
    _create_booking_live_locations_table()
    _create_booking_related_tables()
    UserNotification.__table__.create(bind=test_engine)


def _signup_driver() -> str:
    response = client.post(
        "/v1/api/travel/auth/signup",
        json={
            "phone": "012345678",
            "full_name": "Driver Demo",
            "role": "driver",
            "password": "strongpass123",
            "avatar_url": "data:image/jpeg;base64,dummy_driver_avatar_bytes",
        },
    )
    assert response.status_code == 201
    return response.json()["token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _signup_passenger(phone: str = "098765432") -> str:
    response = client.post(
        "/v1/api/travel/auth/signup",
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
        "/v1/api/travel/vehicles",
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
        "/v1/api/travel/trips",
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


def test_vehicle_type_is_derived_from_seat_type() -> None:
    token = _signup_driver()

    response = client.post(
        "/v1/api/travel/vehicles",
        headers=_auth_headers(token),
        json={
            "plate_number": "2AB-8888",
            "seat_type": 4,
            "vehicle_type": "bus",
            "model": "Prius",
            "color": "White",
            "company_name": "Demo Travel",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["seat_type"] == 4
    assert body["vehicle_type"] == "sedan"


def test_vehicle_type_is_rederived_when_seat_type_changes() -> None:
    token = _signup_driver()
    vehicle_id = _create_vehicle(token)

    response = client.patch(
        f"/v1/api/travel/vehicles/{vehicle_id}",
        headers=_auth_headers(token),
        json={
            "plate_number": "2AB-9999",
            "seat_type": 30,
            "vehicle_type": "sedan",
            "model": "County",
            "color": "White",
            "company_name": "Demo Travel",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["seat_type"] == 30
    assert body["vehicle_type"] == "minibus"


def test_trusted_device_login_issues_new_token_without_password() -> None:
    signup_response = client.post(
        "/v1/api/travel/auth/signup",
        json={
            "phone": "011111111",
            "full_name": "Trusted Device User",
            "role": "passenger",
            "password": "strongpass123",
            "device_id": "android:trusted-device-1",
            "device_platform": "android",
            "device_name": "Samsung Galaxy",
            "avatar_url": None,
        },
    )
    assert signup_response.status_code == 201
    trusted_device = signup_response.json()["trusted_device"]
    assert trusted_device is not None
    assert trusted_device["device_platform"] == "android"
    assert trusted_device["device_secret"]

    login_response = client.post(
        "/v1/api/travel/auth/device-login",
        json={
            "device_id": "android:trusted-device-1",
            "device_secret": trusted_device["device_secret"],
        },
    )
    assert login_response.status_code == 200
    body = login_response.json()
    assert body["token"]
    assert body["user"]["phone"] == "011111111"
    assert body["trusted_device"] is None


def test_app_config_returns_google_places_key_from_backend_env(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "backend-places-key")
    monkeypatch.delenv("GOOGLE_PLACES_API_KEY_ANDROID", raising=False)
    monkeypatch.delenv("GOOGLE_PLACES_API_KEY_IOS", raising=False)

    response = client.get("/v1/api/travel/app-config")

    assert response.status_code == 200
    assert response.json() == {
        "google_places_api_key": "backend-places-key",
        "google_places_api_key_android": "backend-places-key",
        "google_places_api_key_ios": "backend-places-key",
    }


def test_app_config_returns_platform_google_places_keys(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "shared-places-key")
    monkeypatch.setenv("GOOGLE_PLACES_API_KEY_ANDROID", "android-places-key")
    monkeypatch.setenv("GOOGLE_PLACES_API_KEY_IOS", "ios-places-key")

    response = client.get("/v1/api/travel/app-config")

    assert response.status_code == 200
    assert response.json() == {
        "google_places_api_key": "shared-places-key",
        "google_places_api_key_android": "android-places-key",
        "google_places_api_key_ios": "ios-places-key",
    }


def test_app_config_returns_only_platform_keys_when_shared_is_missing(monkeypatch) -> None:
    monkeypatch.delenv("GOOGLE_PLACES_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_PLACES_API_KEY_ANDROID", "android-places-key")
    monkeypatch.setenv("GOOGLE_PLACES_API_KEY_IOS", "ios-places-key")

    response = client.get("/v1/api/travel/app-config")

    assert response.status_code == 200
    assert response.json() == {
        "google_places_api_key": None,
        "google_places_api_key_android": "android-places-key",
        "google_places_api_key_ios": "ios-places-key",
    }


def test_app_config_omits_google_places_key_when_backend_env_missing(monkeypatch) -> None:
    monkeypatch.delenv("GOOGLE_PLACES_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_PLACES_API_KEY_ANDROID", raising=False)
    monkeypatch.delenv("GOOGLE_PLACES_API_KEY_IOS", raising=False)

    response = client.get("/v1/api/travel/app-config")

    assert response.status_code == 200
    assert response.json() == {
        "google_places_api_key": None,
        "google_places_api_key_android": None,
        "google_places_api_key_ios": None,
    }


def test_signup_succeeds_without_trusted_device_when_table_is_missing() -> None:
    TrustedDevice.__table__.drop(bind=test_engine, checkfirst=True)

    signup_response = client.post(
        "/v1/api/travel/auth/signup",
        json={
            "phone": "022222222",
            "full_name": "Fallback Signup User",
            "role": "passenger",
            "password": "strongpass123",
            "device_id": "android:signup-fallback-1",
            "device_platform": "android",
            "device_name": "Fallback Phone",
            "avatar_url": None,
        },
    )

    assert signup_response.status_code == 201
    body = signup_response.json()
    assert body["token"]
    assert body["user"]["phone"] == "022222222"
    assert body["trusted_device"] is None


def test_login_succeeds_without_trusted_device_when_table_is_missing() -> None:
    signup_response = client.post(
        "/v1/api/travel/auth/signup",
        json={
            "phone": "033333333",
            "full_name": "Fallback Login User",
            "role": "passenger",
            "password": "strongpass123",
            "avatar_url": None,
        },
    )
    assert signup_response.status_code == 201

    TrustedDevice.__table__.drop(bind=test_engine, checkfirst=True)

    login_response = client.post(
        "/v1/api/travel/auth/login",
        json={
            "phone": "033333333",
            "password": "strongpass123",
            "device_id": "android:login-fallback-1",
            "device_platform": "android",
            "device_name": "Fallback Login Device",
        },
    )

    assert login_response.status_code == 200
    body = login_response.json()
    assert body["token"]
    assert body["user"]["phone"] == "033333333"
    assert body["trusted_device"] is None


def test_create_trip_with_structured_route_and_stops_round_trips_through_read_and_update() -> None:
    token = _signup_driver()
    vehicle_id = _create_vehicle(token)

    create_response = client.post(
        "/v1/api/travel/trips",
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
        f"/v1/api/travel/trips/{trip_id}",
        headers=_auth_headers(token),
        json={"price_per_seat": 6},
    )

    assert update_response.status_code == 200
    updated_trip = update_response.json()
    assert updated_trip["price_per_seat"] == 6.0
    assert updated_trip["departure_route"]["commune_code"] == "060101"
    assert updated_trip["pickup_stop"]["label"] == "ផ្សារកំពង់ធំ"
    assert updated_trip["dropoff_stop"]["label"] == "មុខរបងវត្ត"

    get_response = client.get(f"/v1/api/travel/trips/{trip_id}")

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
        "/v1/api/travel/trips",
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
        "/v1/api/travel/trips",
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
        "/v1/api/travel/trips",
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
        "/v1/api/travel/trips/search",
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
        "/v1/api/travel/trips/search",
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
        "/v1/api/travel/trips/search",
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
        "/v1/api/travel/trips",
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
        f"/v1/api/travel/trips/{trip_id}/complete",
        headers=_auth_headers(token),
    )

    assert complete_response.status_code == 400
    assert (
        complete_response.json()["detail"]
        == "Trip cannot be completed before its departure time"
    )

    get_response = client.get(f"/v1/api/travel/trips/{trip_id}")
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "scheduled"


def test_complete_trip_posts_wallet_cash_collected_as_khr(monkeypatch) -> None:
    frozen_now = datetime(2026, 6, 15, 11, 45, 0)
    monkeypatch.setattr(travel_routes, "phnom_penh_now", lambda: frozen_now)

    driver_token = _signup_driver()
    passenger_token = _signup_passenger()
    vehicle_id = _create_vehicle(driver_token)

    create_response = client.post(
        "/v1/api/travel/trips",
        headers=_auth_headers(driver_token),
        json={
            "vehicle_id": vehicle_id,
            "departure_province": "ភ្នំពេញ",
            "destination_province": "កណ្ដាល",
            "departure_time": "2026-06-15T11:30:00",
            "price_per_seat": 12000,
            "total_seats": 4,
            "available_seats": 3,
            "status": "active",
        },
    )
    assert create_response.status_code == 201
    trip_id = create_response.json()["id"]

    passenger_id = client.get(
        "/v1/api/travel/auth/me",
        headers=_auth_headers(passenger_token),
    ).json()["id"]
    booking_id = str(uuid4())
    _insert_booking(
        booking_id,
        trip_id,
        passenger_id,
        "passenger_boarded",
        total_price=12000,
    )

    complete_response = client.post(
        f"/v1/api/travel/trips/{trip_id}/complete",
        headers=_auth_headers(driver_token),
    )

    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "completed"

    with TestingSessionLocal() as db:
        wallet_entry = db.execute(select(DriverWalletEntry)).scalar_one()
        assert wallet_entry.cash_collected_khr == 12000
        assert wallet_entry.service_fee_khr == 4000


def test_search_trips_repairs_future_trip_marked_completed_too_early(monkeypatch) -> None:
    frozen_now = datetime(2026, 6, 15, 11, 19, 0)
    tz = ZoneInfo("Asia/Phnom_Penh")
    monkeypatch.setattr(travel_routes, "phnom_penh_now", lambda: frozen_now)
    monkeypatch.setattr(travel_routes, "_local_now", lambda _: frozen_now)

    token = _signup_driver()
    vehicle_id = _create_vehicle(token)

    create_response = client.post(
        "/v1/api/travel/trips",
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
        "/v1/api/travel/trips/search",
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

    get_response = client.get(f"/v1/api/travel/trips/{trip_id}")
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "scheduled"


def test_create_booking_creates_driver_notification() -> None:
    driver_token = _signup_driver()
    passenger_token = _signup_passenger()
    vehicle_id = _create_vehicle(driver_token)

    trip_response = client.post(
        "/v1/api/travel/trips",
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
        "/v1/api/travel/notifications",
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
        "/v1/api/travel/trips",
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
        "/v1/api/travel/notifications",
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
        "/v1/api/travel/trips",
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
        f"/v1/api/travel/bookings/{booking_id}/driver-arrived",
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
        "/v1/api/travel/trips",
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
        f"/v1/api/travel/bookings/{booking_id}/passenger-live-location",
        headers=_auth_headers(passenger_token),
        json={"lat": 11.5565, "lng": 104.9283, "accuracy_m": 10},
    )
    assert loc_resp.status_code == 200

    response = client.post(
        f"/v1/api/travel/bookings/{booking_id}/driver-arrived",
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
        "/v1/api/travel/trips",
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
        f"/v1/api/travel/bookings/{booking_id}/driver-arrived",
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
        "/v1/api/travel/trips",
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
        f"/v1/api/travel/bookings/{booking_id}/passenger-live-location",
        headers=_auth_headers(passenger_token),
        json={"lat": 11.5650, "lng": 104.9350, "accuracy_m": 10},
    )
    assert loc_resp.status_code == 200

    response = client.post(
        f"/v1/api/travel/bookings/{booking_id}/driver-arrived",
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
        "/v1/api/travel/trips",
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
        f"/v1/api/travel/bookings/{booking_id}/passenger-live-location",
        headers=_auth_headers(passenger_token),
        json={"lat": 11.5565, "lng": 104.9283, "accuracy_m": 10},
    )
    assert loc_resp.status_code == 200

    # Advance time past the 60s TTL
    stale_time = datetime(2026, 6, 15, 11, 32, 0)  # 90s later
    monkeypatch.setattr(travel_routes, "phnom_penh_now", lambda: stale_time)

    response = client.post(
        f"/v1/api/travel/bookings/{booking_id}/driver-arrived",
        headers=_auth_headers(driver_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pickup_status"] == "driver_arrived"
    assert data["driver_arrived_at"] is not None
    assert data["passenger_live_location"] is None


def test_boarding_request_requires_driver_arrived_first(monkeypatch) -> None:
    frozen_now = datetime(2026, 6, 15, 11, 30, 0)
    monkeypatch.setattr(travel_routes, "phnom_penh_now", lambda: frozen_now)

    driver_token = _signup_driver()
    _signup_passenger()
    vehicle_id = _create_vehicle(driver_token)

    trip_response = client.post(
        "/v1/api/travel/trips",
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
        f"/v1/api/travel/bookings/{booking_id}/boarding/request",
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
        "/v1/api/travel/trips",
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
        f"/v1/api/travel/bookings/{booking_id}/passenger-live-location",
        headers=_auth_headers(passenger_token),
        json={"lat": 11.5565, "lng": 104.9283, "accuracy_m": 10},
    )
    assert loc_resp.status_code == 200

    # Step 1: Driver arrives (has departure_lat/lng = live location)
    arrived = client.post(
        f"/v1/api/travel/bookings/{booking_id}/driver-arrived",
        headers=_auth_headers(driver_token),
    )
    assert arrived.status_code == 200

    # Step 2: Driver requests boarding (immediately auto-confirming/boarding)
    request_resp = client.post(
        f"/v1/api/travel/bookings/{booking_id}/boarding/request",
        headers=_auth_headers(driver_token),
    )
    assert request_resp.status_code == 200
    assert request_resp.json()["driver_requested_boarding_at"] is not None
    assert request_resp.json()["passenger_confirmed_boarding_at"] is not None
    assert request_resp.json()["pickup_status"] == "passenger_boarded"

    # Step 3: Check boarding status from passenger side
    status_resp = client.get(
        f"/v1/api/travel/bookings/{booking_id}/boarding/status",
        headers=_auth_headers(passenger_token),
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "confirmed"

    # Step 4: Passenger confirms boarding (should be idempotent success)
    confirm_resp = client.post(
        f"/v1/api/travel/bookings/{booking_id}/boarding/passenger-confirm",
        headers=_auth_headers(passenger_token),
    )
    assert confirm_resp.status_code == 200
    data = confirm_resp.json()
    assert data["pickup_status"] == "passenger_boarded"
    assert data["status"] == "confirmed"
    assert data["passenger_confirmed_boarding_at"] is not None

    # Step 5: Check notification was created for driver
    notifications = client.get(
        "/v1/api/travel/notifications",
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
        "/v1/api/travel/trips",
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
        f"/v1/api/travel/bookings/{booking_id}/passenger-live-location",
        headers=_auth_headers(passenger_token),
        json={"lat": 11.5565, "lng": 104.9283, "accuracy_m": 10},
    )
    assert loc_resp.status_code == 200

    # Mark arrived
    arrived_resp = client.post(
        f"/v1/api/travel/bookings/{booking_id}/driver-arrived",
        headers=_auth_headers(driver_token),
    )
    assert arrived_resp.status_code == 200

    # Request boarding (automatically boards passenger)
    request_resp = client.post(
        f"/v1/api/travel/bookings/{booking_id}/boarding/request",
        headers=_auth_headers(driver_token),
    )
    assert request_resp.status_code == 200

    # Passenger declines/cancels boarding - should fail with 400 because they are already boarded
    cancel_resp = client.post(
        f"/v1/api/travel/bookings/{booking_id}/boarding/cancel",
        headers=_auth_headers(passenger_token),
    )
    assert cancel_resp.status_code == 400
    assert "already been confirmed" in cancel_resp.json()["detail"]


def test_booking_passenger_contact_scoped_to_booking_users(monkeypatch) -> None:
    frozen_now = datetime(2026, 6, 15, 11, 30, 0)
    monkeypatch.setattr(travel_routes, "phnom_penh_now", lambda: frozen_now)

    driver_token = _signup_driver()
    passenger_token = _signup_passenger("098765436")
    other_passenger_token = _signup_passenger("098765437")
    vehicle_id = _create_vehicle(driver_token)

    trip_response = client.post(
        "/v1/api/travel/trips",
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
        f"/v1/api/travel/bookings/{booking_id}/passenger-live-location",
        headers=_auth_headers(passenger_token),
        json={"lat": 11.5565, "lng": 104.9283, "accuracy_m": 8},
    )
    assert live_location_resp.status_code == 200

    driver_bookings = client.get(
        "/v1/api/travel/bookings",
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
        f"/v1/api/travel/bookings/{booking_id}",
        headers=_auth_headers(passenger_token),
    )
    assert passenger_booking.status_code == 200
    assert passenger_booking.json()["passenger_contact"]["phone"] == "098765436"
    assert passenger_booking.json()["passenger_live_location"]["lat"] == 11.5565
    assert passenger_booking.json()["passenger_live_location"]["lng"] == 104.9283

    denied = client.get(
        f"/v1/api/travel/bookings/{booking_id}",
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
        "/v1/api/travel/trips",
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
        f"/v1/api/travel/bookings/{booking_id}/passenger-live-location",
        headers=_auth_headers(passenger_token),
        json={"lat": 11.5565, "lng": 104.9283, "accuracy_m": 10},
    )
    assert loc_resp.status_code == 200
    assert loc_resp.json()["status"] == "ok"

    with test_engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE bookings SET pickup_status = ? WHERE id = ?",
            ("driver_arrived", UUID(booking_id).hex),
        )

    arrived_loc_resp = client.put(
        f"/v1/api/travel/bookings/{booking_id}/passenger-live-location",
        headers=_auth_headers(passenger_token),
        json={"lat": 11.5566, "lng": 104.9284, "accuracy_m": 9},
    )
    assert arrived_loc_resp.status_code == 200
    assert arrived_loc_resp.json()["status"] == "ok"

    with test_engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE bookings SET pickup_status = ? WHERE id = ?",
            ("passenger_boarded", UUID(booking_id).hex),
        )

    boarded_loc_resp = client.put(
        f"/v1/api/travel/bookings/{booking_id}/passenger-live-location",
        headers=_auth_headers(passenger_token),
        json={"lat": 11.5567, "lng": 104.9285, "accuracy_m": 8},
    )
    assert boarded_loc_resp.status_code == 400
    assert boarded_loc_resp.json()["detail"] == "Location tracking is only active before boarding"

    with test_engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE bookings SET pickup_status = ? WHERE id = ?",
            ("driver_arrived", UUID(booking_id).hex),
        )

    # Driver checks proximity
    prox_resp = client.get(
        f"/v1/api/travel/bookings/{booking_id}/proximity",
        headers=_auth_headers(driver_token),
    )
    assert prox_resp.status_code == 200
    prox = prox_resp.json()
    assert prox["driver_location_fresh"] is True
    assert prox["passenger_location_fresh"] is True
    assert prox["distance_m"] > 0
    assert prox["within_threshold"] is True


def test_live_location_websocket_accepts_passenger_location(monkeypatch) -> None:
    monkeypatch.setattr(live_ws_routes, "SessionLocal", TestingSessionLocal)

    driver_token = _signup_driver()
    passenger_token = _signup_passenger("098765438")
    other_passenger_token = _signup_passenger("098765439")
    vehicle_id = _create_vehicle(driver_token)

    trip_response = client.post(
        "/v1/api/travel/trips",
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
            select(User).where(User.phone == "098765438")
        ).scalar_one()
        booking_id = str(uuid4())
        _insert_booking(booking_id, trip_id, str(passenger.id))

    passenger_user = live_ws_routes._user_from_token(passenger_token)
    other_passenger_user = live_ws_routes._user_from_token(other_passenger_token)
    driver_user = live_ws_routes._user_from_token(driver_token)
    assert passenger_user is not None
    assert other_passenger_user is not None
    assert driver_user is not None
    assert live_ws_routes._authorized_rooms(
        passenger_user,
        trip_id,
        booking_id,
    ) == {f"booking:{booking_id}"}
    assert live_ws_routes._authorized_rooms(
        driver_user,
        trip_id,
        booking_id,
    ) == {f"trip:{trip_id}", f"booking:{booking_id}"}
    assert live_ws_routes._authorized_rooms(
        other_passenger_user,
        trip_id,
        booking_id,
    ) == set()

    broadcast_rooms: list[str] = []

    async def capture_broadcast(room: str, payload: dict) -> None:
        broadcast_rooms.append(room)

    monkeypatch.setattr(live_ws_routes.hub, "broadcast", capture_broadcast)
    asyncio.run(
        live_ws_routes._handle_driver_location(
            driver_user,
            {
                "trip_id": trip_id,
                "lat": 11.5564,
                "lng": 104.9282,
            },
        )
    )
    assert f"trip:{trip_id}" in broadcast_rooms
    assert f"booking:{booking_id}" in broadcast_rooms

    with client.websocket_connect(
        f"/v1/api/travel/live/ws?token={passenger_token}&booking_id={booking_id}&trip_id={trip_id}"
    ) as passenger_ws:
        passenger_ws.send_json(
            {
                "type": "passenger_location",
                "booking_id": booking_id,
                "lat": 11.5565,
                "lng": 104.9283,
                "accuracy_m": 8,
            }
        )

    with TestingSessionLocal() as db:
        booking = db.execute(
            select(Booking)
            .options(selectinload(Booking.live_location))
            .where(Booking.id == UUID(booking_id))
        ).scalar_one()

    assert booking.live_location is not None
    assert float(booking.live_location.lat) == 11.5565
    assert float(booking.live_location.lng) == 104.9283
    assert float(booking.live_location.accuracy_m) == 8


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
        "/v1/api/travel/bookings",
        headers=_auth_headers(driver_token),
    )
    assert driver_bookings.status_code == 200
    expired_booking = next(item for item in driver_bookings.json() if item["id"] == booking_id)
    assert expired_booking["status"] == "cancelled"
    assert expired_booking["trip"]["status"] == "cancelled"

    passenger_active = client.get(
        "/v1/api/travel/bookings/active",
        headers=_auth_headers(passenger_token),
    )
    assert passenger_active.status_code == 200
    assert passenger_active.json()["booking"] is None


def test_active_booking_keeps_past_departure_pickup_trackable(monkeypatch) -> None:
    frozen_now = datetime(2026, 6, 20, 12, 0, 0)
    monkeypatch.setattr(travel_routes, "phnom_penh_now", lambda: frozen_now)

    driver_token = _signup_driver()
    passenger_token = _signup_passenger()
    vehicle_id = _create_vehicle(driver_token)
    trip_id = _create_trip_for_test(
        driver_token,
        vehicle_id,
        departure_time="2026-06-20T11:00:00",
    )

    with TestingSessionLocal() as db:
        passenger = db.execute(
            select(User).where(User.role == "passenger")
        ).scalar_one()
        booking_id = str(uuid4())
        _insert_booking(
            booking_id,
            trip_id,
            str(passenger.id),
            pickup_status="driver_arrived",
        )
        trip = db.get(Trip, UUID(trip_id))
        assert trip is not None
        trip.live_location_expires_at = datetime(2026, 6, 20, 13, 0, 0)
        db.commit()

    passenger_active = client.get(
        "/v1/api/travel/bookings/active",
        headers=_auth_headers(passenger_token),
    )

    assert passenger_active.status_code == 200
    active_booking = passenger_active.json()["booking"]
    assert active_booking is not None
    assert active_booking["id"] == booking_id
    assert active_booking["pickup_status"] == "driver_arrived"


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
        "/v1/api/travel/driver/trips",
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


def test_list_bookings_tolerates_duplicate_future_repeated_trips(monkeypatch) -> None:
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

        duplicate_departure = datetime(2026, 6, 20, 7, 30, 0)
        for _ in range(2):
            db.add(
                Trip(
                    driver_id=trip.driver_id,
                    vehicle_id=trip.vehicle_id,
                    departure_province=trip.departure_province,
                    destination_province=trip.destination_province,
                    departure_time=duplicate_departure,
                    departure_lat=trip.departure_lat,
                    departure_lng=trip.departure_lng,
                    repeat_mode="daily",
                    auto_repeat_weekly=False,
                    recurring_departure_time=trip.recurring_departure_time,
                    has_return_schedule=False,
                    price_per_seat=trip.price_per_seat,
                    total_seats=trip.total_seats,
                    available_seats=trip.total_seats,
                    status="scheduled",
                )
            )
        db.commit()

    response = client.get(
        "/v1/api/travel/bookings",
        headers=_auth_headers(driver_token),
    )

    assert response.status_code == 200
    assert response.json() == []


def test_recommended_trips_passenger():
    driver_token = _signup_driver()
    vehicle_id = _create_vehicle(driver_token)
    passenger_token = _signup_passenger()

    # Create an upcoming trip
    from datetime import datetime, timedelta
    future_time = (datetime.now() + timedelta(days=5)).isoformat()
    trip_id = _create_trip_for_test(driver_token, vehicle_id, departure_time=future_time)

    # Call endpoint with passenger auth
    response = client.get(
        "/v1/api/passenger/recommended-trips",
        headers=_auth_headers(passenger_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(trip["id"] == trip_id for trip in data)

    # Call endpoint with driver auth (should be forbidden)
    denied = client.get(
        "/v1/api/passenger/recommended-trips",
        headers=_auth_headers(driver_token),
    )
    assert denied.status_code == 403


def test_list_passenger_trips():
    driver_token = _signup_driver()
    vehicle_id = _create_vehicle(driver_token)
    passenger_token = _signup_passenger()

    from datetime import datetime, timedelta

    first_trip_id = _create_trip_for_test(
        driver_token,
        vehicle_id,
        departure_time=(datetime.now() + timedelta(days=2)).isoformat(),
    )
    second_trip_id = _create_trip_for_test(
        driver_token,
        vehicle_id,
        departure_time=(datetime.now() + timedelta(days=4)).isoformat(),
    )

    response = client.get(
        "/v1/api/passenger/trips",
        headers=_auth_headers(passenger_token),
    )
    assert response.status_code == 200
    data = response.json()
    ids = [trip["id"] for trip in data]
    assert first_trip_id in ids
    assert second_trip_id in ids

    limited = client.get(
        "/v1/api/passenger/trips",
        params={"limit": 1},
        headers=_auth_headers(passenger_token),
    )
    assert limited.status_code == 200
    assert len(limited.json()) == 1

    denied = client.get(
        "/v1/api/passenger/trips",
        headers=_auth_headers(driver_token),
    )
    assert denied.status_code == 403


def test_find_trips_now_endpoint() -> None:
    # 1. Create a driver and a vehicle
    token = _signup_driver()
    vehicle_id = _create_vehicle(token)
    
    # 2. Add an Address catalog entry for a village near Kampong Thom (12.71123, 104.88991)
    db = override_get_db().__next__()
    try:
        from app.models import Address
        Address.__table__.create(bind=test_engine, checkfirst=True)
        # First clear addresses
        db.query(Address).delete()
        # Add country, province, district, commune, village
        country = Address(id=1, code="855", name="Cambodia", description="កម្ពុជា", type="country")
        province = Address(id=2, code="06", name="Kampong Thom Province", description="កំពង់ធំ", type="province", parent_code="855")
        district = Address(id=3, code="0601", name="Stueng Saen", description="ស្ទឹងសែន", type="district", parent_code="06")
        commune = Address(id=4, code="060101", name="Kampong Roteh", description="កំពង់រទេះ", type="commune", parent_code="0601")
        village = Address(
            id=5,
            code="06010101",
            name="Village A",
            description="ភូមិ A",
            type="village",
            parent_code="060101",
            latitude=12.71123,
            longitude=104.88991,
            reference="National Road 6",
        )
        db.add_all([country, province, district, commune, village])
        db.commit()
    finally:
        db.close()
        
    # 3. Create a trip from Kampong Thom to Phnom Penh
    from datetime import timedelta
    create_response = client.post(
        "/v1/api/travel/trips",
        headers=_auth_headers(token),
        json={
            "vehicle_id": vehicle_id,
            "departure_province": "Kampong Thom",
            "destination_province": "Phnom Penh",
            "departure_time": (datetime.now() + timedelta(hours=2)).isoformat(),
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
        },
    )
    assert create_response.status_code == 201
    trip_id = create_response.json()["id"]
    
    # 4. Search for trips near Kampong Thom (12.71123, 104.88991)
    response = client.get(
        "/v1/api/travel/trips/find-now",
        params={
            "lat": 12.71123,
            "lng": 104.88991,
        },
        headers=_auth_headers(token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["passenger_province"] == "កំពង់ធំ"
    assert "National Road 6" in data["passenger_road"]
    assert len(data["trips"]) == 1
    assert data["trips"][0]["id"] == trip_id

    # A selected destination is broader than the passenger's detected route.
    # This trip reaches Phnom Penh from a different corridor and must still be
    # offered so the passenger can decide whether its route is suitable.
    alternate_route_response = client.post(
        "/v1/api/travel/trips",
        headers=_auth_headers(token),
        json={
            "vehicle_id": vehicle_id,
            "departure_province": "Battambang",
            "destination_province": "Phnom Penh",
            "departure_time": (datetime.now() + timedelta(hours=3)).isoformat(),
            "departure_lat": 13.0957,
            "departure_lng": 103.2022,
            "repeat_mode": "none",
            "auto_repeat_weekly": False,
            "has_return_schedule": False,
            "price_per_seat": 7,
            "total_seats": 15,
            "available_seats": 15,
            "status": "scheduled",
        },
    )
    assert alternate_route_response.status_code == 201
    alternate_trip_id = alternate_route_response.json()["id"]

    destination_response = client.get(
        "/v1/api/travel/trips/find-now",
        params={
            "lat": 12.71123,
            "lng": 104.88991,
            "destination_province": "Phnom Penh",
        },
        headers=_auth_headers(token),
    )
    assert destination_response.status_code == 200
    destination_trip_ids = {
        trip["id"] for trip in destination_response.json()["trips"]
    }
    assert destination_trip_ids == {trip_id, alternate_trip_id}


def test_find_trips_now_prioritizes_nearest_active_trip() -> None:
    near_token = _signup_driver()
    near_vehicle_id = _create_vehicle(near_token)
    far_signup = client.post(
        "/v1/api/travel/auth/signup",
        json={
            "phone": "012345679",
            "full_name": "Driver Far",
            "role": "driver",
            "password": "strongpass123",
            "avatar_url": "data:image/jpeg;base64,dummy_driver_avatar_bytes",
        },
    )
    assert far_signup.status_code == 201
    far_token = far_signup.json()["token"]
    far_vehicle_response = client.post(
        "/v1/api/travel/vehicles",
        headers=_auth_headers(far_token),
        json={
            "plate_number": "2AB-9998",
            "seat_type": 15,
            "vehicle_type": "Van",
            "model": "County",
            "color": "White",
            "company_name": "Demo Travel",
        },
    )
    assert far_vehicle_response.status_code == 201
    far_vehicle_id = far_vehicle_response.json()["id"]

    db = override_get_db().__next__()
    try:
        from app.models import Address

        Address.__table__.create(bind=test_engine, checkfirst=True)
        db.query(Address).delete()
        db.add_all(
            [
                Address(
                    id=1,
                    code="855",
                    name="Cambodia",
                    description="កម្ពុជា",
                    type="country",
                ),
                Address(
                    id=2,
                    code="06",
                    name="Kampong Thom Province",
                    description="កំពង់ធំ",
                    type="province",
                    parent_code="855",
                ),
                Address(
                    id=3,
                    code="0601",
                    name="Stueng Saen",
                    description="ស្ទឹងសែន",
                    type="district",
                    parent_code="06",
                ),
                Address(
                    id=4,
                    code="060101",
                    name="Kampong Roteh",
                    description="កំពង់រទេះ",
                    type="commune",
                    parent_code="0601",
                ),
                Address(
                    id=5,
                    code="06010101",
                    name="Village A",
                    description="ភូមិ A",
                    type="village",
                    parent_code="060101",
                    latitude=12.71123,
                    longitude=104.88991,
                    reference="National Road 6",
                ),
            ]
        )
        db.commit()
    finally:
        db.close()

    from datetime import timedelta

    near_response = client.post(
        "/v1/api/travel/trips",
        headers=_auth_headers(near_token),
        json={
            "vehicle_id": near_vehicle_id,
            "departure_province": "Kampong Thom",
            "destination_province": "Phnom Penh",
            "departure_time": (datetime.now() - timedelta(minutes=20)).isoformat(),
            "departure_lat": 12.71123,
            "departure_lng": 104.88991,
            "price_per_seat": 5,
            "total_seats": 15,
            "available_seats": 12,
            "status": "active",
            "departure_route": {
                "province_code": "06",
                "province_name": "កំពង់ធំ",
                "district_code": "0601",
                "district_name": "ស្ទឹងសែន",
                "commune_code": "060101",
                "commune_name": "ស្ទឹងសែន",
            },
        },
    )
    assert near_response.status_code == 201
    near_trip_id = near_response.json()["id"]

    far_response = client.post(
        "/v1/api/travel/trips",
        headers=_auth_headers(far_token),
        json={
            "vehicle_id": far_vehicle_id,
            "departure_province": "Kampong Thom",
            "destination_province": "Phnom Penh",
            "departure_time": (datetime.now() - timedelta(minutes=10)).isoformat(),
            "departure_lat": 12.71123,
            "departure_lng": 104.88991,
            "price_per_seat": 6,
            "total_seats": 15,
            "available_seats": 9,
            "status": "active",
            "departure_route": {
                "province_code": "06",
                "province_name": "កំពង់ធំ",
                "district_code": "0601",
                "district_name": "ស្ទឹងសែន",
                "commune_code": "060101",
                "commune_name": "ស្ទឹងសែន",
            },
        },
    )
    assert far_response.status_code == 201
    far_trip_id = far_response.json()["id"]

    db = override_get_db().__next__()
    try:
        near_trip = db.execute(select(Trip).where(Trip.id == UUID(near_trip_id))).scalar_one()
        far_trip = db.execute(select(Trip).where(Trip.id == UUID(far_trip_id))).scalar_one()
        near_trip.live_lat = 12.719
        near_trip.live_lng = 104.892
        far_trip.live_lat = 13.05
        far_trip.live_lng = 104.90
        db.commit()
    finally:
        db.close()

    response = client.get(
        "/v1/api/travel/trips/find-now",
        params={
            "lat": 12.71123,
            "lng": 104.88991,
        },
        headers=_auth_headers(near_token),
    )

    assert response.status_code == 200
    trips = response.json()["trips"]
    assert len(trips) == 2
    assert trips[0]["id"] == near_trip_id
    assert trips[1]["id"] == far_trip_id


def test_signup_driver_avatar_validation() -> None:
    # 1. Driver signup without avatar_url should fail with 400
    response = client.post(
        "/v1/api/travel/auth/signup",
        json={
            "phone": "099999991",
            "full_name": "Driver No Avatar",
            "role": "driver",
            "password": "strongpass123",
            "avatar_url": None,
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Drivers must upload a face image"

    # 2. Driver signup with empty avatar_url should fail with 400
    response = client.post(
        "/v1/api/travel/auth/signup",
        json={
            "phone": "099999991",
            "full_name": "Driver Empty Avatar",
            "role": "driver",
            "password": "strongpass123",
            "avatar_url": "   ",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Drivers must upload a face image"

    # 3. Driver signup with avatar_url should succeed with 201
    response = client.post(
        "/v1/api/travel/auth/signup",
        json={
            "phone": "099999991",
            "full_name": "Driver With Avatar",
            "role": "driver",
            "password": "strongpass123",
            "avatar_url": "data:image/jpeg;base64,dummy_driver_avatar_bytes",
        },
    )
    assert response.status_code == 201
    assert response.json()["user"]["avatar_url"] == "data:image/jpeg;base64,dummy_driver_avatar_bytes"


def test_signup_passenger_avatar_is_optional_and_returned() -> None:
    response = client.post(
        "/v1/api/travel/auth/signup",
        json={
            "phone": "099999992",
            "full_name": "Passenger With Avatar",
            "role": "passenger",
            "password": "strongpass123",
            "avatar_url": "data:image/png;base64,dummy_passenger_avatar_bytes",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["avatar_url"] == "data:image/png;base64,dummy_passenger_avatar_bytes"

    me_response = client.get(
        "/v1/api/travel/auth/me",
        headers=_auth_headers(body["token"]),
    )
    assert me_response.status_code == 200
    assert me_response.json()["avatar_url"] == "data:image/png;base64,dummy_passenger_avatar_bytes"


def test_update_current_user_profile() -> None:
    token = _signup_passenger("099999993")
    avatar_url = "data:image/png;base64,updated_passenger_avatar_bytes"

    response = client.patch(
        "/v1/api/travel/auth/me",
        headers=_auth_headers(token),
        json={
            "full_name": "Updated Passenger",
            "avatar_url": avatar_url,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "Updated Passenger"
    assert body["avatar_url"] == avatar_url

    me_response = client.get("/v1/api/travel/auth/me", headers=_auth_headers(token))
    assert me_response.status_code == 200
    assert me_response.json()["full_name"] == "Updated Passenger"
    assert me_response.json()["avatar_url"] == avatar_url


def test_update_current_user_profile_can_clear_avatar() -> None:
    token = _signup_passenger("099999994")

    response = client.patch(
        "/v1/api/travel/auth/me",
        headers=_auth_headers(token),
        json={
            "avatar_url": "   ",
        },
    )

    assert response.status_code == 200
    assert response.json()["avatar_url"] is None


def test_create_trip_validates_promo_discount_percent_cannot_exceed_100() -> None:
    token = _signup_driver()
    vehicle_id = _create_vehicle(token)

    # Test > 100% (e.g. 120%)
    response = client.post(
        "/v1/api/travel/trips",
        headers=_auth_headers(token),
        json={
            "vehicle_id": vehicle_id,
            "departure_province": "Phnom Penh",
            "destination_province": "Siem Reap",
            "departure_time": "2026-06-25T07:30:00",
            "price_per_seat": 10,
            "currency": "USD",
            "total_seats": 4,
            "available_seats": 4,
            "promotion_label": "Super Discount",
            "promotion_discount_percent": 120,
        },
    )
    assert response.status_code in (400, 422)

    # Test <= 100% (e.g. 20%)
    valid_response = client.post(
        "/v1/api/travel/trips",
        headers=_auth_headers(token),
        json={
            "vehicle_id": vehicle_id,
            "departure_province": "Phnom Penh",
            "destination_province": "Siem Reap",
            "departure_time": "2026-06-25T07:30:00",
            "price_per_seat": 10,
            "currency": "USD",
            "total_seats": 4,
            "available_seats": 4,
            "promotion_label": "Super Discount",
            "promotion_discount_percent": 20,
        },
    )
    assert valid_response.status_code == 201
    assert valid_response.json()["promotion"]["discount_percent"] == 20
