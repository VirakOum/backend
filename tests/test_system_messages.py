import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

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

from sqlalchemy.ext.compiler import compiles
from sqlalchemy import ARRAY

@compiles(ARRAY, "sqlite")
def compile_array_sqlite(type_, compiler, **kw):
    return "TEXT"

from app.main import app
from app.db import Base, get_db

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
Base.metadata.create_all(bind=test_engine)

client = TestClient(app)


def test_system_messages_crud_and_active_flow():
    # 1. Create a system message via admin endpoint
    create_payload = {
        "title": "Road Closure Alert",
        "body": "National Road 6 undergoing maintenance. Expect minor delays.",
        "target_role": "all",
        "message_type": "warning",
        "is_active": True,
        "is_pinned": True,
        "broadcast_to_notifications": False,
    }
    resp = client.post("/v1/api/travel/admin/messages", json=create_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["title"] == "Road Closure Alert"
    assert data["message_type"] == "warning"
    assert data["is_pinned"] is True
    msg_id = data["id"]

    # 2. List admin messages
    list_resp = client.get("/v1/api/travel/admin/messages")
    assert list_resp.status_code == 200
    messages = list_resp.json()
    assert any(m["id"] == msg_id for m in messages)

    # 3. Get active system messages from travel API for driver role
    active_resp = client.get("/v1/api/travel/messages/active?role=driver")
    assert active_resp.status_code == 200
    active_msgs = active_resp.json()["messages"]
    assert len(active_msgs) >= 1
    assert active_msgs[0]["id"] == msg_id

    # 4. Toggle active state
    toggle_resp = client.post(f"/v1/api/travel/admin/messages/{msg_id}/toggle-active")
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["is_active"] is False

    # Verify deactivated message no longer returns in active messages
    active_resp2 = client.get("/v1/api/travel/messages/active?role=driver")
    assert active_resp2.status_code == 200
    active_msgs2 = active_resp2.json()["messages"]
    assert not any(m["id"] == msg_id for m in active_msgs2)

    # 5. Delete system message
    del_resp = client.delete(f"/v1/api/travel/admin/messages/{msg_id}")
    assert del_resp.status_code == 204


def test_register_push_token():
    # 1. Signup a user to get auth header
    phone = "012888999"
    signup_resp = client.post(
        "/v1/api/travel/auth/signup",
        json={
            "phone": phone,
            "full_name": "Push User",
            "role": "passenger",
            "password": "Password123!",
        },
    )
    if signup_resp.status_code == 400:
        login_resp = client.post(
            "/v1/api/travel/auth/login",
            json={"phone": phone, "password": "Password123!"},
        )
        token = login_resp.json()["token"]
    else:
        token = signup_resp.json()["token"]

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Register push token
    resp = client.post(
        "/v1/api/travel/devices/push-token",
        json={
            "push_token": "fcm_test_token_abcdef1234567890",
            "platform": "android",
            "device_id": "test_device_001",
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "ok"
    assert data["registered"] is True
    assert data["push_token"] == "fcm_test_token_abcdef1234567890"
