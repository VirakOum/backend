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
from app.models import User, Trip, Booking, Vehicle, PassengerQuickPlace, DriverWallet, DriverWalletEntry
from app.auth import hash_password

test_engine = create_engine(
    "sqlite+pysqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    prev_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    if prev_override is not None:
        app.dependency_overrides[get_db] = prev_override
    else:
        app.dependency_overrides.pop(get_db, None)
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



def test_edit_passenger():
    with TestingSessionLocal() as db:
        passenger = User(
            phone="012999001",
            full_name="Original Name",
            role="passenger",
            password_hash=hash_password("Pass123!"),
            is_verified=False,
            is_active=True,
        )
        db.add(passenger)
        db.commit()
        db.refresh(passenger)
        p_id = passenger.id

    res = client.patch(f"/v1/api/travel/admin/passengers/{p_id}", json={
        "full_name": "Updated Name",
        "is_verified": True,
        "phone": "012999002"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["full_name"] == "Updated Name"
    assert data["is_verified"] is True
    assert data["phone"] == "012999002"

    with TestingSessionLocal() as db:
        p = db.get(User, p_id)
        assert p.full_name == "Updated Name"
        assert p.is_verified is True
        assert p.phone == "012999002"


def test_close_and_reopen_passenger_account():
    with TestingSessionLocal() as db:
        passenger = User(
            phone="012888001",
            full_name="Active Passenger",
            role="passenger",
            password_hash=hash_password("Pass123!"),
            is_verified=True,
            is_active=True,
        )
        db.add(passenger)
        db.commit()
        db.refresh(passenger)
        p_id = passenger.id

    # Verify initial login works
    login_res = client.post("/v1/api/travel/auth/login", json={
        "phone": "012888001",
        "password": "Pass123!"
    })
    assert login_res.status_code == 200
    token = login_res.json()["token"]

    # Close account via admin endpoint
    close_res = client.post(f"/v1/api/travel/admin/passengers/{p_id}/close-account")
    assert close_res.status_code == 200
    assert close_res.json()["is_active"] is False

    # Check user is now is_active == False
    with TestingSessionLocal() as db:
        p = db.get(User, p_id)
        assert p.is_active is False

    # Old token should now fail
    me_res = client.get("/v1/api/travel/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 401

    # Login should now fail with 403 Forbidden
    login_fail = client.post("/v1/api/travel/auth/login", json={
        "phone": "012888001",
        "password": "Pass123!"
    })
    assert login_fail.status_code == 403

    # Reopen account
    reopen_res = client.post(f"/v1/api/travel/admin/passengers/{p_id}/reopen-account")
    assert reopen_res.status_code == 200
    assert reopen_res.json()["is_active"] is True

    # Login should now succeed again
    login_again = client.post("/v1/api/travel/auth/login", json={
        "phone": "012888001",
        "password": "Pass123!"
    })
    assert login_again.status_code == 200


def test_delete_driver_via_drivers_endpoint():
    with TestingSessionLocal() as db:
        driver = User(
            phone="012777001",
            full_name="Driver Heng",
            role="driver",
            password_hash=hash_password("Pass123!"),
            is_verified=True,
        )
        passenger = User(
            phone="012777002",
            full_name="Passenger Dara",
            role="passenger",
            password_hash=hash_password("Pass123!"),
            is_verified=True,
        )
        db.add_all([driver, passenger])
        db.commit()
        db.refresh(driver)
        db.refresh(passenger)

        vehicle = Vehicle(
            owner_id=driver.id,
            plate_number="2AB-9999",
            seat_type=4,
            model="Camry",
            color="Silver",
        )
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)

        # Create outward trip
        outward_trip = Trip(
            driver_id=driver.id,
            vehicle_id=vehicle.id,
            departure_province="Phnom Penh",
            destination_province="Siem Reap",
            departure_time=datetime.now(timezone.utc),
            price_per_seat=45000,
            currency="KHR",
            total_seats=4,
            available_seats=3,
            status="scheduled",
        )
        db.add(outward_trip)
        db.commit()
        db.refresh(outward_trip)

        # Create return trip linked by return_trip_id
        return_trip = Trip(
            driver_id=driver.id,
            vehicle_id=vehicle.id,
            return_trip_id=outward_trip.id,
            departure_province="Siem Reap",
            destination_province="Phnom Penh",
            departure_time=datetime.now(timezone.utc),
            price_per_seat=45000,
            currency="KHR",
            total_seats=4,
            available_seats=4,
            status="scheduled",
        )
        db.add(return_trip)
        db.commit()
        db.refresh(return_trip)

        # Set outward trip's return_trip_id to create cycle / reference
        outward_trip.return_trip_id = return_trip.id
        db.commit()

        # Create a booking on outward trip
        booking = Booking(
            trip_id=outward_trip.id,
            passenger_id=passenger.id,
            seat_numbers=[1],
            total_price=45000,
            currency="KHR",
            payment_method="cash",
            payment_status="pending",
            pickup_status="pending",
            status="pending",
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)

        # Create driver wallet and entry
        wallet = DriverWallet(
            driver_id=driver.id,
            total_owed_khr=5000,
            total_owed_usd=0,
            is_locked=False,
        )
        db.add(wallet)
        db.commit()

        wallet_entry = DriverWalletEntry(
            driver_id=driver.id,
            booking_id=booking.id,
            trip_id=outward_trip.id,
            entry_type="trip_service_fee",
            payment_method="cash",
            membership_code_snapshot="normal",
            membership_label_snapshot="Normal",
            service_fee_khr=5000,
            status="owed",
        )
        db.add(wallet_entry)
        db.commit()

        driver_id = driver.id
        passenger_id = passenger.id
        vehicle_id = vehicle.id
        outward_trip_id = outward_trip.id
        return_trip_id = return_trip.id
        booking_id = booking.id

    # 1. Reject passenger on driver delete endpoint (400)
    bad_res = client.delete(f"/v1/api/travel/admin/drivers/{passenger_id}")
    assert bad_res.status_code == 400
    assert "Only driver accounts can be deleted" in bad_res.json()["detail"]

    # 2. Reject non-existent user on driver delete endpoint (404)
    fake_id = uuid.uuid4()
    not_found_res = client.delete(f"/v1/api/travel/admin/drivers/{fake_id}")
    assert not_found_res.status_code == 404

    # 3. Successfully delete driver via driver endpoint
    del_res = client.delete(f"/v1/api/travel/admin/drivers/{driver_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"
    assert del_res.json()["id"] == str(driver_id)

    # 4. Verify DB state
    with TestingSessionLocal() as db:
        # Driver is deleted
        assert db.get(User, driver_id) is None
        # Vehicle is deleted
        assert db.get(Vehicle, vehicle_id) is None
        # Trips are deleted
        assert db.get(Trip, outward_trip_id) is None
        assert db.get(Trip, return_trip_id) is None
        # Bookings on driver's trip are deleted
        assert db.get(Booking, booking_id) is None
        # Wallet and entries are deleted
        assert db.query(DriverWallet).filter(DriverWallet.driver_id == driver_id).first() is None
        assert db.query(DriverWalletEntry).filter(DriverWalletEntry.driver_id == driver_id).all() == []
        # Passenger account still exists
        assert db.get(User, passenger_id) is not None
