from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import ARRAY

@compiles(ARRAY, "sqlite")
def compile_array_sqlite(type_, compiler, **kw):
    return "TEXT"

import json
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db import get_db
from app.models import AuthToken, Booking, TelegramOtpSession, Trip, TrustedDevice, User, Vehicle

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
    User.__table__.create(bind=test_engine, checkfirst=True)
    AuthToken.__table__.create(bind=test_engine, checkfirst=True)
    TrustedDevice.__table__.create(bind=test_engine, checkfirst=True)
    Vehicle.__table__.create(bind=test_engine, checkfirst=True)
    Trip.__table__.create(bind=test_engine, checkfirst=True)
    Booking.__table__.create(bind=test_engine, checkfirst=True)
    TelegramOtpSession.__table__.create(bind=test_engine, checkfirst=True)
    try:
        pass
    except Exception:
        pass
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
    assert "--taxi-accent" in css_res.text

    js_res = client.get("/miniapp/js/miniapp.js")
    assert js_res.status_code == 200
    assert ("javascript" in js_res.headers["content-type"] or "text/plain" in js_res.headers["content-type"])
    assert "window.Telegram" in js_res.text


def test_telegram_miniapp_quick_book_and_my_bookings():
    client = TestClient(app)

    # 1. Quick book a ride
    payload = {
        "trip_id": str(uuid4()),
        "seat_count": 2,
        "passenger_name": "Sophea Traveller",
        "phone": "0966519115",
        "telegram_user_id": "123456789",
        "telegram_chat_id": "123456789",
        "telegram_username": "sophea_tg",
        "pickup_note": "Sokha Hotel Lobby",
        "payment_method": "cash"
    }

    res = client.post("/v1/api/travel/telegram/miniapp/quick-book", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "confirmed"
    assert data["reference_code"].startswith("MT-")
    assert data["passenger_name"] == "Sophea Traveller"
    assert data["phone"] == "0966519115"
    assert data["seat_count"] == 2
    assert data["total_price"] > 0
    assert data["payment_method"] == "cash"

    # 2. Retrieve My Bookings for this phone
    my_res = client.get("/v1/api/travel/telegram/miniapp/my-bookings?phone=0966519115")
    assert my_res.status_code == 200
    bookings = my_res.json()
    assert isinstance(bookings, list)


def test_telegram_miniapp_custom_request():
    client = TestClient(app)

    payload = {
        "departure_province": "Phnom Penh",
        "destination_province": "Siem Reap",
        "passenger_name": "Dara Roth",
        "phone": "012888999",
        "requested_seats": 4,
        "note": "Depart at 2:00 PM VIP SUV",
        "telegram_user_id": "987654321"
    }

    res = client.post("/v1/api/travel/telegram/miniapp/custom-request", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "received"
    assert data["reference_code"].startswith("REQ-")


def test_telegram_bot_commands_support_miniapp():
    client = TestClient(app)

    # Trigger webhook with /book command
    update = {
        "update_id": 999901,
        "message": {
            "message_id": 1,
            "date": 1730000000,
            "chat": {"id": 123456, "type": "private"},
            "from": {"id": 123456, "first_name": "Tester", "username": "tester_tg"},
            "text": "/book"
        }
    }

    res = client.post("/v1/api/travel/auth/telegram-otp/webhook", json=update)
    assert res.status_code == 200
    assert res.json() == {"ok": True}
