import json
import pytest
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
from app.models import User, Vehicle, AuthToken

test_engine = create_engine(
    "sqlite+pysqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_delete_passenger_account():
    # 1. Sign up passenger
    signup_res = client.post(
        "/v1/api/travel/auth/signup",
        json={
            "full_name": "Test Passenger",
            "phone": "012345001",
            "password": "Password123!",
            "role": "passenger",
        },
    )
    assert signup_res.status_code == 201
    token = signup_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Check profile exists
    me_res = client.get("/v1/api/travel/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["phone"] == "012345001"

    # 3. Delete account
    del_res = client.delete("/v1/api/travel/auth/me", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["message"] == "Account successfully deleted"

    # 4. Verify auth fails now
    after_res = client.get("/v1/api/travel/auth/me", headers=headers)
    assert after_res.status_code == 401


def test_delete_driver_account_with_vehicle():
    # 1. Sign up driver
    signup_res = client.post(
        "/v1/api/travel/auth/signup",
        json={
            "full_name": "Test Driver",
            "phone": "012345002",
            "password": "Password123!",
            "role": "driver",
            "avatar_url": "data:image/png;base64,samplefaceimage",
        },
    )
    assert signup_res.status_code == 201
    token = signup_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Add vehicle
    veh_res = client.post(
        "/v1/api/travel/vehicles",
        headers=headers,
        json={
            "plate_number": "2AB-9999",
            "seat_type": 4,
            "model": "Toyota Prius",
        },
    )
    assert veh_res.status_code == 201

    # 3. Delete account
    del_res = client.delete("/v1/api/travel/auth/me", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["message"] == "Account successfully deleted"

    # 4. Verify user and vehicle are gone from db
    with TestingSessionLocal() as db:
        user = db.query(User).filter(User.phone == "012345002").first()
        assert user is None
        veh = db.query(Vehicle).filter(Vehicle.plate_number == "2AB-9999").first()
        assert veh is None
