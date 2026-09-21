import asyncio
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.main import app
from app.db import get_db
from app.models import AppRuntimeSetting, AuthToken, Trip, TrustedDevice, User, Vehicle, phnom_penh_now

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

def _create_bookings_table() -> None:
    with test_engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS bookings (
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

app.dependency_overrides[get_db] = override_get_db
User.__table__.create(bind=test_engine, checkfirst=True)
AuthToken.__table__.create(bind=test_engine, checkfirst=True)
TrustedDevice.__table__.create(bind=test_engine, checkfirst=True)
Vehicle.__table__.create(bind=test_engine, checkfirst=True)
Trip.__table__.create(bind=test_engine, checkfirst=True)
AppRuntimeSetting.__table__.create(bind=test_engine, checkfirst=True)
_create_bookings_table()

client = TestClient(app)

def test_trip_search_window_4_hours():
    app.dependency_overrides[get_db] = override_get_db
    db = TestingSessionLocal()
    
    # Create driver
    driver = User(
        id=uuid4(),
        phone="012345678",
        role="driver",
        full_name="Test Driver",
        password_hash="hash",
    )
    db.add(driver)
    db.flush()

    vehicle = Vehicle(
        id=uuid4(),
        owner_id=driver.id,
        plate_number="2AA-1234",
        model="Camry",
        seat_type=4,
    )
    db.add(vehicle)
    db.flush()

    now = phnom_penh_now()
    
    # Trip 1: Departed 2 hours ago (should be found)
    dep_2h_ago = now - timedelta(hours=2)
    trip_2h = Trip(
        id=uuid4(),
        driver_id=driver.id,
        vehicle_id=vehicle.id,
        departure_province="ភ្នំពេញ",
        destination_province="បាត់ដំបង",
        departure_time=dep_2h_ago,
        total_seats=4,
        available_seats=4,
        price_per_seat=40000,
        currency="KHR",
        status="scheduled",
    )
    db.add(trip_2h)

    # Trip 2: Departed 3.5 hours ago (should be found)
    dep_3_5h_ago = now - timedelta(hours=3, minutes=30)
    trip_3_5h = Trip(
        id=uuid4(),
        driver_id=driver.id,
        vehicle_id=vehicle.id,
        departure_province="ភ្នំពេញ",
        destination_province="បាត់ដំបង",
        departure_time=dep_3_5h_ago,
        total_seats=4,
        available_seats=4,
        price_per_seat=40000,
        currency="KHR",
        status="scheduled",
    )
    db.add(trip_3_5h)

    # Trip 3: Departed 5 hours ago (should NOT be found)
    dep_5h_ago = now - timedelta(hours=5)
    trip_5h = Trip(
        id=uuid4(),
        driver_id=driver.id,
        vehicle_id=vehicle.id,
        departure_province="ភ្នំពេញ",
        destination_province="បាត់ដំបង",
        departure_time=dep_5h_ago,
        total_seats=4,
        available_seats=4,
        price_per_seat=40000,
        currency="KHR",
        status="scheduled",
    )
    db.add(trip_5h)
    db.commit()

    # Search trips: schedule="now"
    resp = client.get(
        "/v1/api/travel/trips/search",
        params={
            "departure_province": "ភ្នំពេញ",
            "destination_province": "បាត់ដំបង",
            "journey_date": now.strftime("%Y-%m-%d"),
            "schedule": "now",
        },
    )
    assert resp.status_code == 200, resp.text
    found_trips = resp.json()
    found_ids = [t["id"] for t in found_trips]

    assert str(trip_2h.id) in found_ids, "Trip departed 2h ago should be found"
    assert str(trip_3_5h.id) in found_ids, "Trip departed 3.5h ago should be found"
    assert str(trip_5h.id) not in found_ids, "Trip departed 5h ago should NOT be found"

    # Verify that departure_time in DB is untouched
    db.refresh(trip_2h)
    assert trip_2h.departure_time == dep_2h_ago
    db.refresh(trip_3_5h)
    assert trip_3_5h.departure_time == dep_3_5h_ago

    # Test passenger trips endpoint
    passenger = User(
        id=uuid4(),
        phone="088888888",
        role="passenger",
        full_name="Test Passenger",
        password_hash="hash",
    )
    db.add(passenger)
    db.commit()

    from app.auth import issue_token
    token = issue_token(db, passenger)

    p_resp = client.get(
        "/v1/api/passenger/trips",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert p_resp.status_code == 200, p_resp.text
    p_trips = p_resp.json()
    p_ids = [t["id"] for t in p_trips]
    assert str(trip_2h.id) in p_ids, "Passenger trips should include trip departed 2h ago"
    assert str(trip_3_5h.id) in p_ids, "Passenger trips should include trip departed 3.5h ago"
    assert str(trip_5h.id) not in p_ids, "Passenger trips should NOT include trip departed 5h ago"

    db.close()
