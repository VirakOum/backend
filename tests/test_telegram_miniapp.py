from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import ARRAY

@compiles(ARRAY, "sqlite")
def compile_array_sqlite(type_, compiler, **kw):
    return "TEXT"

import json
from datetime import timedelta
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db import get_db
from app.models import (
    AuthToken,
    Booking,
    DriverMembership,
    SupportTicket,
    TelegramOtpSession,
    Trip,
    TrustedDevice,
    User,
    UserNotification,
    Vehicle,
    phnom_penh_now,
)

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


def setup_module():
    for tbl in [
        User.__table__,
        AuthToken.__table__,
        TrustedDevice.__table__,
        Vehicle.__table__,
        Trip.__table__,
        Booking.__table__,
        UserNotification.__table__,
        SupportTicket.__table__,
        DriverMembership.__table__,
        TelegramOtpSession.__table__,
    ]:
        tbl.create(bind=test_engine, checkfirst=True)
    app.dependency_overrides[get_db] = override_get_db


def teardown_module():
    app.dependency_overrides.clear()


def test_telegram_miniapp_static_routes():
    client = TestClient(app)

    # 1. Main entry points
    for path in ["/miniapp", "/miniapp/", "/telegram/miniapp", "/telegram/app"]:
        res = client.get(path)
        assert res.status_code == 200, f"Failed for {path}"
        assert "text/html" in res.headers["content-type"]
        assert "MyTravel Taxi | Telegram Mini App" in res.text
        assert "telegram-web-app.js" in res.text

    # 2. CSS and JS assets
    css_res = client.get("/miniapp/css/miniapp.css")
    assert css_res.status_code == 200
    assert "text/css" in css_res.headers["content-type"]

    js_res = client.get("/miniapp/js/miniapp.js")
    assert js_res.status_code == 200
    assert ("javascript" in js_res.headers["content-type"] or "text/plain" in js_res.headers["content-type"])
    assert "window.Telegram" in js_res.text
    # Ensure no fake demo trips exist in JS
    assert "trip-demo-1" not in js_res.text
    assert "renderFallbackTrips" not in js_res.text


def test_telegram_miniapp_quick_book_and_my_bookings_real_db():
    client = TestClient(app)

    # 1. Non-existent trip must return 404 (no fake fallback booking)
    bad_res = client.post(
        "/v1/api/travel/telegram/miniapp/quick-book",
        json={
            "trip_id": str(uuid4()),
            "seat_count": 1,
            "passenger_name": "Sophea Traveller",
            "phone": "0966519115",
        },
    )
    assert bad_res.status_code == 404

    # 2. Seed a real driver, vehicle, and scheduled trip in DB
    db = TestingSessionLocal()
    try:
        driver = User(
            phone="011223344",
            full_name="Channary Driver",
            role="driver",
            password_hash="hashed_pw",
            is_verified=True,
        )
        db.add(driver)
        db.flush()

        vehicle = Vehicle(
            owner_id=driver.id,
            vehicle_type="SUV",
            model="Toyota Highlander",
            plate_number="2CD-8899",
            seat_type=4,
        )
        db.add(vehicle)
        db.flush()

        trip = Trip(
            driver_id=driver.id,
            vehicle_id=vehicle.id,
            departure_province="ភ្នំពេញ",
            destination_province="សៀមរាប",
            departure_time=phnom_penh_now() + timedelta(hours=3),
            price_per_seat=48000,
            currency="KHR",
            total_seats=4,
            available_seats=4,
            status="scheduled",
        )
        db.add(trip)
        db.commit()
        real_trip_id = str(trip.id)
    finally:
        db.close()

    # 3. Verify GET /v1/api/travel/trips/public finds the Khmer-named trip even when queried with English province names
    pub_res = client.get("/v1/api/travel/trips/public?departure_province=Phnom%20Penh&destination_province=Siem%20Reap")
    assert pub_res.status_code == 200
    pub_trips = pub_res.json()
    assert any(t["id"] == real_trip_id for t in pub_trips)

    # 4. Book specific seats on the real trip
    payload = {
        "trip_id": real_trip_id,
        "seat_count": 2,
        "seat_numbers": [2, 3],
        "passenger_name": "Sophea Traveller",
        "phone": "0966519115",
        "telegram_user_id": "123456789",
        "telegram_chat_id": "123456789",
        "telegram_username": "sophea_tg",
        "pickup_note": "Wat Phnom Landmark",
        "payment_method": "cash",
    }

    res = client.post("/v1/api/travel/telegram/miniapp/quick-book", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "confirmed"
    assert data["trip_id"] == real_trip_id
    assert data["seat_numbers"] == [2, 3]
    assert data["seat_count"] == 2
    assert data["total_price"] == 96000.0
    assert data["currency"] == "KHR"
    assert data["driver_name"] == "Channary Driver"
    assert data["driver_phone"] == "011223344"
    assert data["vehicle_model"] == "Toyota Highlander"
    assert data["plate_number"] == "2CD-8899"

    # 5. Retrieve My Bookings by phone and by telegram_user_id
    my_res_phone = client.get("/v1/api/travel/telegram/miniapp/my-bookings?phone=0966519115")
    assert my_res_phone.status_code == 200
    bookings_by_phone = my_res_phone.json()
    assert len(bookings_by_phone) == 1
    assert bookings_by_phone[0]["booking_id"] == data["booking_id"]
    assert bookings_by_phone[0]["seat_numbers"] == [2, 3]

    my_res_tg = client.get("/v1/api/travel/telegram/miniapp/my-bookings?telegram_user_id=123456789")
    assert my_res_tg.status_code == 200
    bookings_by_tg = my_res_tg.json()
    assert len(bookings_by_tg) == 1
    assert bookings_by_tg[0]["booking_id"] == data["booking_id"]


def test_telegram_miniapp_custom_request_persists_support_ticket():
    client = TestClient(app)

    payload = {
        "departure_province": "Phnom Penh",
        "destination_province": "Siem Reap",
        "passenger_name": "Dara Roth",
        "phone": "012888999",
        "requested_seats": 4,
        "note": "Depart at 2:00 PM VIP SUV",
        "telegram_user_id": "987654321",
    }

    res = client.post("/v1/api/travel/telegram/miniapp/custom-request", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "open"
    assert data["reference_code"].startswith("REQ-")
    assert "ticket_id" in data


def test_telegram_bot_commands_support_miniapp():
    client = TestClient(app)

    update = {
        "update_id": 999901,
        "message": {
            "message_id": 1,
            "date": 1730000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "first_name": "Tester", "username": "tester_tg"},
            "text": "/book",
        },
    }

    res = client.post("/v1/api/travel/auth/telegram-otp/webhook", json=update)
    assert res.status_code == 200
    assert res.json() == {"ok": True}
