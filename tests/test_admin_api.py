import json
from datetime import datetime
from uuid import uuid4
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
from app.models import User, Vehicle, Trip, Booking, DriverWallet, DriverMembership, AppRuntimeSetting

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


def setup_function() -> None:
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)


def test_admin_settings_get_and_post() -> None:
    # 1. Get default settings
    response = client.get("/travel/admin/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["enable_digital_payment"] is False
    assert data["auto_lock_on_limit"] is True
    assert data["driver_cash_debt_limit_usd"] == 20.0
    assert data["driver_cash_debt_limit_khr"] == 80000

    # 2. Update settings
    update_payload = {
        "enable_digital_payment": True,
        "auto_lock_on_limit": False,
        "driver_cash_debt_limit_usd": 50.0,
        "driver_cash_debt_limit_khr": 200000,
    }
    post_response = client.post("/travel/admin/settings", json=update_payload)
    assert post_response.status_code == 200
    updated_data = post_response.json()
    assert updated_data["enable_digital_payment"] is True
    assert updated_data["auto_lock_on_limit"] is False
    assert updated_data["driver_cash_debt_limit_usd"] == 50.0
    assert updated_data["driver_cash_debt_limit_khr"] == 200000


def test_admin_summary() -> None:
    db = TestingSessionLocal()
    
    # Add seed users
    driver = User(
        id=uuid4(),
        phone="012345678",
        full_name="Sok Dara",
        role="driver",
        password_hash="hash",
        is_verified=True,
    )
    passenger = User(
        id=uuid4(),
        phone="098765432",
        full_name="Chan Nary",
        role="passenger",
        password_hash="hash",
        is_verified=False,
    )
    db.add_all([driver, passenger])
    db.commit()

    # Get summary
    response = client.get("/travel/admin/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_drivers"] == 1
    assert data["total_passengers"] == 1
    assert data["active_trips"] == 0
    assert data["pending_bookings"] == 0
    assert data["total_trips"] == 0
    assert data["total_bookings"] == 0
    assert data["seat_occupancy_rate"] == 0.0
    db.close()


def test_admin_user_management_and_toggle_verification() -> None:
    db = TestingSessionLocal()
    user_id = uuid4()
    user = User(
        id=user_id,
        phone="012345678",
        full_name="Sok Dara",
        role="driver",
        password_hash="hash",
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.close()

    # 1. Get users list
    response = client.get("/travel/admin/users")
    assert response.status_code == 200
    users = response.json()
    assert len(users) == 1
    assert users[0]["full_name"] == "Sok Dara"
    assert users[0]["is_verified"] is False

    # 2. Toggle verification
    toggle_resp = client.post(f"/travel/admin/users/{user_id}/toggle-verification")
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["is_verified"] is True

    # 3. Verify changes persist
    response2 = client.get("/travel/admin/users")
    assert response2.json()[0]["is_verified"] is True


def test_admin_driver_lock_and_membership() -> None:
    db = TestingSessionLocal()
    driver_id = uuid4()
    driver = User(
        id=driver_id,
        phone="012000333",
        full_name="Preap Sovath",
        role="driver",
        password_hash="hash",
        is_verified=True,
    )
    db.add(driver)
    db.commit()

    wallet = DriverWallet(
        driver_id=driver_id,
        service_fee_owed_usd=0.0,
        total_owed_usd=0.0,
        admin_locked=False,
        is_locked=False,
    )
    db.add(wallet)
    db.commit()
    db.close()

    # 1. Toggle Lock (Lock driver)
    lock_resp = client.post(f"/travel/admin/users/{driver_id}/toggle-wallet-lock?reason=SuspiciousActivity")
    assert lock_resp.status_code == 200
    assert lock_resp.json()["admin_locked"] is True
    assert lock_resp.json()["is_locked"] is True
    assert lock_resp.json()["locked_reason"] == "SuspiciousActivity"

    # 2. Toggle Lock again (Unlock driver)
    unlock_resp = client.post(f"/travel/admin/users/{driver_id}/toggle-wallet-lock")
    assert unlock_resp.status_code == 200
    assert unlock_resp.json()["admin_locked"] is False
    assert unlock_resp.json()["is_locked"] is False

    # 3. Change membership tier to VIP
    membership_resp = client.post(f"/travel/admin/users/{driver_id}/change-membership?tier=vip")
    assert membership_resp.status_code == 200
    assert membership_resp.json()["tier"] == "vip"

    # 4. Settle wallet debt (Even though it is 0, test success)
    settle_resp = client.post("/travel/admin/wallet/settle", json={"driver_id": str(driver_id), "notes": "Office visit"})
    assert settle_resp.status_code == 200
    assert float(settle_resp.json()["wallet"]["total_owed_usd"]) == 0.0


def test_admin_revenue_api() -> None:
    from app.models import DriverWalletEntry, Trip, Booking
    from app.routes.admin import phnom_penh_now
    
    db = TestingSessionLocal()
    now = phnom_penh_now()
    driver_id = uuid4()
    trip_id = uuid4()
    booking_id = uuid4()
    booking_id2 = uuid4()
    
    # Add a mock driver
    driver = User(
        id=driver_id,
        phone="099888777",
        full_name="Driver Joe",
        role="driver",
        password_hash="hash",
        is_verified=True,
    )
    db.add(driver)
    
    # Add a mock trip
    trip = Trip(
        id=trip_id,
        driver_id=driver_id,
        departure_province="Phnom Penh",
        destination_province="Siem Reap",
        departure_time=now,
        return_departure_time=now,
        status="active",
        price_per_seat=10000,
        available_seats=4,
        total_seats=4,
    )
    db.add(trip)
    
    # Add mock bookings
    booking1 = Booking(
        id=booking_id,
        trip_id=trip_id,
        passenger_id=driver_id,
        seat_numbers=[1],
        total_price=10.0,
        status="confirmed",
    )
    booking2 = Booking(
        id=booking_id2,
        trip_id=trip_id,
        passenger_id=driver_id,
        seat_numbers=[2],
        total_price=20.0,
        status="confirmed",
    )
    db.add_all([booking1, booking2])
    db.commit()
    
    # Add wallet entries (income points)
    entry1 = DriverWalletEntry(
        id=uuid4(),
        driver_id=driver_id,
        trip_id=trip_id,
        booking_id=booking_id,
        membership_code_snapshot="normal",
        membership_label_snapshot="Normal User",
        service_fee_usd=1.0,
        service_fee_khr=4000,
        status="owed",
        posted_at=now,
    )
    entry2 = DriverWalletEntry(
        id=uuid4(),
        driver_id=driver_id,
        trip_id=trip_id,
        booking_id=booking_id2,
        membership_code_snapshot="normal",
        membership_label_snapshot="Normal User",
        service_fee_usd=2.0,
        service_fee_khr=8000,
        status="settled",
        posted_at=now,
    )
    db.add_all([entry1, entry2])
    db.commit()
    db.close()
    
    response = client.get("/travel/admin/revenue")
    assert response.status_code == 200
    data = response.json()
    
    # Verify aggregated sums
    assert data["total_usd"] == 3.0
    assert data["total_khr"] == 12000
    assert data["today_usd"] == 3.0
    assert data["today_khr"] == 12000
    
    # Verify points lists contain records
    assert len(data["daily"]) > 0
    assert data["daily"][0]["amount_usd"] == 3.0
    assert data["daily"][0]["amount_khr"] == 12000


def test_admin_trip_edit_and_delete() -> None:
    from app.models import Trip
    from app.routes.admin import phnom_penh_now
    
    db = TestingSessionLocal()
    now = phnom_penh_now()
    driver_id = uuid4()
    trip_id = uuid4()
    
    # Setup mock user and trip
    driver = User(
        id=driver_id,
        phone="099111222",
        full_name="Driver Tom",
        role="driver",
        password_hash="hash",
        is_verified=True,
    )
    trip = Trip(
        id=trip_id,
        driver_id=driver_id,
        departure_province="Phnom Penh",
        destination_province="Kampot",
        departure_time=now,
        price_per_seat=12000.0,
        total_seats=10,
        available_seats=10,
        status="scheduled"
    )
    db.add_all([driver, trip])
    db.commit()
    db.close()
    
    # 1. Update Trip details
    update_payload = {
        "status": "active",
        "price_per_seat": 15000.0,
        "total_seats": 12,
        "available_seats": 8
    }
    update_resp = client.put(f"/travel/admin/trips/{trip_id}", json=update_payload)
    assert update_resp.status_code == 200
    updated_data = update_resp.json()
    assert updated_data["status"] == "active"
    assert updated_data["price_per_seat"] == 15000.0
    assert updated_data["total_seats"] == 12
    assert updated_data["available_seats"] == 8
    
    # 2. Delete Trip
    delete_resp = client.delete(f"/travel/admin/trips/{trip_id}")
    assert delete_resp.status_code == 204
    
    # 3. Assert deleted
    db = TestingSessionLocal()
    assert db.get(Trip, trip_id) is None
    db.close()


def test_admin_login_endpoint():
    resp = client.post("/travel/admin/login", json={"phone_or_username": "admin", "password": "Admin123!"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["role"] == "admin"

    bad_resp = client.post("/travel/admin/login", json={"phone_or_username": "admin", "password": "WrongPassword"})
    assert bad_resp.status_code == 401


