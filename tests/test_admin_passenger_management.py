import json
import pytest
import uuid
from datetime import datetime, timezone
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
from app.models import User, Trip, Booking, Vehicle, PassengerQuickPlace
from app.auth import hash_password

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


def test_list_and_delete_passenger():
    # 1. Create a passenger and driver directly in DB
    with TestingSessionLocal() as db:
        driver = User(
            phone="012000001",
            full_name="Driver Sok",
            role="driver",
            password_hash=hash_password("Pass123!"),
            is_verified=True,
        )
        passenger = User(
            phone="012000002",
            full_name="Passenger Vanna",
            role="passenger",
            password_hash=hash_password("Pass123!"),
            is_verified=True,
        )
        db.add_all([driver, passenger])
        db.commit()
        db.refresh(driver)
        db.refresh(passenger)

        trip = Trip(
            driver_id=driver.id,
            departure_province="Phnom Penh",
            destination_province="Siem Reap",
            departure_time=datetime.now(timezone.utc),
            price_per_seat=40000,
            currency="KHR",
            total_seats=4,
            available_seats=2,
            status="scheduled",
        )
        db.add(trip)
        db.commit()
        db.refresh(trip)

        booking = Booking(
            trip_id=trip.id,
            passenger_id=passenger.id,
            seat_numbers=[1, 2],
            total_price=80000,
            currency="KHR",
            payment_method="cash",
            payment_status="pending",
            pickup_status="pending",
            status="pending",
        )
        db.add(booking)

        quick_place = PassengerQuickPlace(
            user_id=passenger.id,
            key="home",
            label="Home",
            address_line="Street 2004, Phnom Penh",
            lat=11.5564,
            lng=104.9282,
        )
        db.add(quick_place)
        db.commit()

        passenger_id = passenger.id
        driver_id = driver.id
        trip_id = trip.id

    # 2. Query admin passengers list
    res = client.get("/v1/api/travel/admin/users?role=passenger")
    assert res.status_code == 200
    passengers = res.json()
    assert len(passengers) == 1
    assert passengers[0]["phone"] == "012000002"
    assert passengers[0]["full_name"] == "Passenger Vanna"

    # 3. Query passenger bookings
    bookings_res = client.get(f"/v1/api/travel/admin/passengers/{passenger_id}/bookings")
    assert bookings_res.status_code == 200
    p_bookings = bookings_res.json()
    assert len(p_bookings) == 1
    assert p_bookings[0]["trip_id"] == str(trip_id)
    assert p_bookings[0]["departure_province"] == "Phnom Penh"
    assert p_bookings[0]["seat_numbers"] == [1, 2]

    # 4. Reject deleting driver via passenger endpoint
    bad_res = client.delete(f"/v1/api/travel/admin/passengers/{driver_id}")
    assert bad_res.status_code == 400

    # 5. Delete passenger
    del_res = client.delete(f"/v1/api/travel/admin/passengers/{passenger_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

    # 6. Verify passenger and related quick places and bookings are deleted
    with TestingSessionLocal() as db:
        p_check = db.get(User, passenger_id)
        assert p_check is None

        b_check = db.query(Booking).filter(Booking.passenger_id == passenger_id).all()
        assert len(b_check) == 0

        qp_check = db.query(PassengerQuickPlace).filter(PassengerQuickPlace.user_id == passenger_id).all()
        assert len(qp_check) == 0

        # Trip seats should be restored back from 2 to 4!
        trip_check = db.get(Trip, trip_id)
        assert trip_check is not None
        assert trip_check.available_seats == 4


def test_delete_passenger_via_users_endpoint():
    with TestingSessionLocal() as db:
        passenger = User(
            phone="012000003",
            full_name="Passenger Dara",
            role="passenger",
            password_hash=hash_password("Pass123!"),
            is_verified=False,
        )
        db.add(passenger)
        db.commit()
        db.refresh(passenger)
        p_id = passenger.id

    res = client.delete(f"/v1/api/travel/admin/users/{p_id}")
    assert res.status_code == 200
    assert res.json()["status"] == "success"

    with TestingSessionLocal() as db:
        assert db.get(User, p_id) is None


def test_passenger_not_found():
    random_id = uuid.uuid4()
    res = client.delete(f"/v1/api/travel/admin/passengers/{random_id}")
    assert res.status_code == 404

    bookings_res = client.get(f"/v1/api/travel/admin/passengers/{random_id}/bookings")
    assert bookings_res.status_code == 404
