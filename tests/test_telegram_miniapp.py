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
from app.auth import hash_password
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
    assert res.json().get("ok") is True


def test_telegram_miniapp_register_role_and_link_existing_app_account():
    client = TestClient(app)

    # 1. Check unregistered Telegram user -> registered: False
    me_unreg = client.get("/v1/api/travel/telegram/miniapp/me?telegram_user_id=555000111")
    assert me_unreg.status_code == 200
    assert me_unreg.json()["registered"] is False

    # 2. End-to-end Register as a DRIVER from Telegram Mini App (with vehicle)
    reg_driver_res = client.post(
        "/v1/api/travel/telegram/miniapp/register",
        json={
            "full_name": "Sokha Driver TG",
            "phone": "077889900",
            "role": "driver",
            "telegram_user_id": "555000111",
            "telegram_chat_id": "555000111",
            "telegram_username": "sokha_driver",
            "vehicle_model": "Lexus RX350",
            "plate_number": "2GH-9988",
            "seat_type": 4,
        },
    )
    assert reg_driver_res.status_code == 200
    reg_driver_data = reg_driver_res.json()
    assert reg_driver_data["registered"] is True
    assert reg_driver_data["telegram_linked"] is True
    assert reg_driver_data["user"]["role"] == "driver"
    assert reg_driver_data["auth_token"]
    assert len(reg_driver_data["driver_summary"]["vehicles"]) == 1
    assert reg_driver_data["driver_summary"]["vehicles"][0]["model"] == "Lexus RX350"

    # 3. Verify GET /me by telegram_user_id returns role=driver and driver_summary
    me_driver = client.get("/v1/api/travel/telegram/miniapp/me?telegram_user_id=555000111")
    assert me_driver.status_code == 200
    assert me_driver.json()["registered"] is True
    assert me_driver.json()["user"]["role"] == "driver"

    # 4. Driver publishes a trip directly from the Mini App
    dep_time = (phnom_penh_now() + timedelta(hours=5)).isoformat()
    pub_trip_res = client.post(
        "/v1/api/travel/telegram/miniapp/driver/trips",
        json={
            "telegram_user_id": "555000111",
            "departure_province": "Phnom Penh (រាជធានីភ្នំពេញ)",
            "destination_province": "Battambang (បាត់ដំបង)",
            "departure_time": dep_time,
            "price_per_seat": 45000,
            "currency": "KHR",
            "total_seats": 4,
        },
    )
    assert pub_trip_res.status_code == 200
    pub_trip_data = pub_trip_res.json()
    assert pub_trip_data["status"] == "scheduled"
    assert pub_trip_data["total_seats"] == 4

    # 5. Simulate accounts created in the Mobile App WITHOUT Telegram OTP (User row exists, no TelegramOtpSession)
    db = TestingSessionLocal()
    try:
        app_driver = User(
            phone="015667788",
            full_name="Vannak App User",
            role="driver",
            password_hash=hash_password("AppPassword123"),
            is_verified=False,
        )
        app_passenger = User(
            phone="012345678",
            full_name="Bopha App Passenger",
            role="passenger",
            password_hash=hash_password("PassengerPass123"),
            is_verified=False,
        )
        db.add_all([app_driver, app_passenger])
        db.commit()
    finally:
        db.close()

    # 6. Check phone from Mini App -> detects existing App account created without Telegram
    chk_res = client.post(
        "/v1/api/travel/telegram/miniapp/check-phone",
        json={
            "phone": "015667788",
            "telegram_user_id": "777888999",
        },
    )
    assert chk_res.status_code == 200
    chk_data = chk_res.json()
    assert chk_data["exists"] is True
    assert chk_data["role"] == "driver"
    assert chk_data["full_name"] == "Vannak App User"
    assert chk_data["created_via_app_without_telegram"] is True
    assert chk_data["already_linked_to_this_telegram"] is False

    # 7. GET /me with phone + unlinked telegram_user_id -> returns requires_app_link: True
    me_unlinked = client.get(
        "/v1/api/travel/telegram/miniapp/me?phone=015667788&telegram_user_id=777888999"
    )
    assert me_unlinked.status_code == 200
    me_unlinked_data = me_unlinked.json()
    assert me_unlinked_data["registered"] is True
    assert me_unlinked_data["telegram_linked"] is False
    assert me_unlinked_data["requires_app_link"] is True
    assert me_unlinked_data["account_preview"]["role"] == "driver"

    # 8. Attempting /register on that phone without password or contact verification -> 409 ACCOUNT_EXISTS_IN_APP
    reg_conflict = client.post(
        "/v1/api/travel/telegram/miniapp/register",
        json={
            "full_name": "Vannak App User",
            "phone": "015667788",
            "role": "driver",
            "telegram_user_id": "777888999",
        },
    )
    assert reg_conflict.status_code == 409
    assert "ACCOUNT_EXISTS_IN_APP" in str(reg_conflict.json()["detail"])

    # 9. Link the existing Mobile App account using App Password
    link_res = client.post(
        "/v1/api/travel/telegram/miniapp/link-account",
        json={
            "phone": "015667788",
            "password": "AppPassword123",
            "telegram_user_id": "777888999",
            "telegram_chat_id": "777888999",
        },
    )
    assert link_res.status_code == 200
    link_data = link_res.json()
    assert link_data["telegram_linked"] is True
    assert link_data["account_action"] == "linked_existing_app_account"
    assert link_data["user"]["role"] == "driver"
    assert link_data["user"]["full_name"] == "Vannak App User"

    # 10. Now GET /me with only telegram_user_id=777888999 resolves the linked App account!
    me_after_link = client.get("/v1/api/travel/telegram/miniapp/me?telegram_user_id=777888999")
    assert me_after_link.status_code == 200
    assert me_after_link.json()["registered"] is True
    assert me_after_link.json()["telegram_linked"] is True
    assert me_after_link.json()["user"]["phone"] == "015667788"
    assert me_after_link.json()["user"]["role"] == "driver"

    # 11. Also test Bot Contact Share webhook auto-linking an existing Mobile App passenger account
    contact_update = {
        "update_id": 999902,
        "message": {
            "message_id": 2,
            "date": 1730000010,
            "chat": {"id": 888999000, "type": "private"},
            "from": {"id": 888999000, "first_name": "Bopha", "username": "bopha_kh"},
            "contact": {
                "phone_number": "+85512345678",
                "first_name": "Bopha",
                "user_id": 888999000,
            },
        },
    }
    wh_res = client.post("/v1/api/travel/auth/telegram-otp/webhook", json=contact_update)
    assert wh_res.status_code == 200

    me_bopha = client.get("/v1/api/travel/telegram/miniapp/me?telegram_user_id=888999000")
    assert me_bopha.status_code == 200
    assert me_bopha.json()["registered"] is True
    assert me_bopha.json()["telegram_linked"] is True
    assert me_bopha.json()["user"]["phone"] == "012345678"
    assert me_bopha.json()["user"]["role"] == "passenger"

