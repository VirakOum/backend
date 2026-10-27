import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db import get_db
from app.models import AuthToken, TelegramOtpSession, TrustedDevice, User

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
    TelegramOtpSession.__table__.create(bind=test_engine, checkfirst=True)
    app.dependency_overrides[get_db] = override_get_db


def teardown_module():
    app.dependency_overrides.clear()


def test_telegram_otp_signup_login_and_reset_flow():
    client = TestClient(app)

    # 1. Signup via Telegram OTP (6-digit code)
    req_resp = client.post(
        "/v1/api/travel/auth/telegram-otp/request",
        json={"phone": "012 888 999", "purpose": "signup"},
    )
    assert req_resp.status_code in (200, 201), req_resp.text
    start_data = req_resp.json()
    session_token = start_data["session_token"]
    otp_code = start_data["demo_otp_code"]
    assert start_data["phone"] == "012888999"
    assert otp_code and len(otp_code) == 6

    verify_signup = client.post(
        "/v1/api/travel/auth/telegram-otp/verify",
        json={
            "session_token": session_token,
            "otp_code": otp_code,
            "full_name": "Sokha Telegram",
            "role": "passenger",
            "device_id": "test-device-tg-1",
            "device_platform": "android",
            "device_name": "Pixel 8",
        },
    )
    assert verify_signup.status_code == 200, verify_signup.text
    auth_data = verify_signup.json()
    assert auth_data["token"]
    assert auth_data["user"]["phone"] == "012888999"
    assert auth_data["user"]["is_verified"] is True
    assert auth_data["trusted_device"]["device_secret"]

    # 2. 1-Tap Login via Telegram Contact Share Webhook (no OTP digits typed!)
    login_req = client.post(
        "/v1/api/travel/auth/telegram-otp/request",
        json={"phone": "012888999", "purpose": "login"},
    )
    assert login_req.status_code in (200, 201), login_req.text
    login_session_token = login_req.json()["session_token"]

    # Simulate user tapping Start in Telegram Bot
    wh_start = client.post(
        "/v1/api/travel/auth/telegram-otp/webhook",
        json={
            "update_id": 1001,
            "message": {
                "message_id": 1,
                "chat": {"id": 555666777},
                "from": {"id": 555666777, "username": "sokha_kh"},
                "text": f"/start otp_{login_session_token}",
            },
        },
    )
    assert wh_start.status_code == 200

    # Simulate user tapping "Share Contact" button in Telegram Bot (+855 12 888 999)
    wh_contact = client.post(
        "/v1/api/travel/auth/telegram-otp/webhook",
        json={
            "update_id": 1002,
            "message": {
                "message_id": 2,
                "chat": {"id": 555666777},
                "from": {"id": 555666777, "username": "sokha_kh"},
                "contact": {
                    "phone_number": "+85512888999",
                    "first_name": "Sokha",
                    "user_id": 555666777,
                },
            },
        },
    )
    assert wh_contact.status_code == 200

    # Polling status should now report is_verified == True
    status_resp = client.get(f"/v1/api/travel/auth/telegram-otp/status/{login_session_token}")
    assert status_resp.status_code == 200
    assert status_resp.json()["is_verified"] is True

    # App completes login without sending otp_code
    verify_1tap = client.post(
        "/v1/api/travel/auth/telegram-otp/verify",
        json={"session_token": login_session_token},
    )
    assert verify_1tap.status_code == 200, verify_1tap.text
    assert verify_1tap.json()["user"]["phone"] == "012888999"

    # 3. Reset Password via Telegram OTP
    reset_req = client.post(
        "/v1/api/travel/auth/telegram-otp/request",
        json={"phone": "012888999", "purpose": "reset_password"},
    )
    assert reset_req.status_code in (200, 201)
    reset_data = reset_req.json()

    reset_verify = client.post(
        "/v1/api/travel/auth/telegram-otp/verify",
        json={
            "session_token": reset_data["session_token"],
            "otp_code": reset_data["demo_otp_code"],
            "new_password": "NewStrongPassword123",
        },
    )
    assert reset_verify.status_code == 200, reset_verify.text

    # Confirm standard password login works with the newly reset password
    pwd_login = client.post(
        "/v1/api/travel/auth/login",
        json={"phone": "012888999", "password": "NewStrongPassword123"},
    )
    assert pwd_login.status_code == 200, pwd_login.text
