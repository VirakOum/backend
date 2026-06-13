from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db import get_db
from app.models import AppRuntimeSetting, AuthToken, DriverWallet, Trip, User, Vehicle


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
User.__table__.create(bind=test_engine)
AuthToken.__table__.create(bind=test_engine)
Vehicle.__table__.create(bind=test_engine)
Trip.__table__.create(bind=test_engine)
DriverWallet.__table__.create(bind=test_engine)
AppRuntimeSetting.__table__.create(bind=test_engine)

client = TestClient(app)


def _create_bookings_table() -> None:
    with test_engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TABLE bookings (
                id TEXT PRIMARY KEY,
                trip_id TEXT NOT NULL,
                passenger_id TEXT NOT NULL,
                seat_numbers TEXT NOT NULL,
                total_price NUMERIC NOT NULL,
                payment_method TEXT,
                payment_status TEXT,
                pickup_status TEXT,
                driver_arrived_at DATETIME,
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


def setup_function() -> None:
    app.dependency_overrides[get_db] = override_get_db
    with test_engine.begin() as connection:
        connection.exec_driver_sql("DROP TABLE IF EXISTS bookings")
    Trip.__table__.drop(bind=test_engine, checkfirst=True)
    Vehicle.__table__.drop(bind=test_engine, checkfirst=True)
    DriverWallet.__table__.drop(bind=test_engine, checkfirst=True)
    AppRuntimeSetting.__table__.drop(bind=test_engine, checkfirst=True)
    AuthToken.__table__.drop(bind=test_engine, checkfirst=True)
    User.__table__.drop(bind=test_engine, checkfirst=True)
    User.__table__.create(bind=test_engine)
    AuthToken.__table__.create(bind=test_engine)
    Vehicle.__table__.create(bind=test_engine)
    Trip.__table__.create(bind=test_engine)
    DriverWallet.__table__.create(bind=test_engine)
    AppRuntimeSetting.__table__.create(bind=test_engine)
    _create_bookings_table()


def _signup_driver() -> str:
    response = client.post(
        "/travel/auth/signup",
        json={
            "phone": "012345678",
            "full_name": "Driver Demo",
            "role": "driver",
            "password": "strongpass123",
            "avatar_url": None,
        },
    )
    assert response.status_code == 201
    return response.json()["token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_vehicle(token: str) -> str:
    response = client.post(
        "/travel/vehicles",
        headers=_auth_headers(token),
        json={
            "plate_number": "2AB-9999",
            "seat_type": 15,
            "vehicle_type": "Van",
            "model": "County",
            "color": "White",
            "company_name": "Demo Travel",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_create_trip_with_structured_route_and_stops_round_trips_through_read_and_update() -> None:
    token = _signup_driver()
    vehicle_id = _create_vehicle(token)

    create_response = client.post(
        "/travel/trips",
        headers=_auth_headers(token),
        json={
            "vehicle_id": vehicle_id,
            "departure_province": "Kampong Thom",
            "destination_province": "Phnom Penh",
            "departure_time": "2026-06-06T07:30:00",
            "departure_lat": 12.71123,
            "departure_lng": 104.88991,
            "repeat_mode": "none",
            "auto_repeat_weekly": False,
            "has_return_schedule": False,
            "price_per_seat": 5,
            "total_seats": 15,
            "available_seats": 15,
            "status": "scheduled",
            "departure_route": {
                "province_code": "06",
                "province_name": "កំពង់ធំ",
                "district_code": "0601",
                "district_name": "ស្ទឹងសែន",
                "commune_code": "060101",
                "commune_name": "ស្ទឹងសែន",
            },
            "destination_route": {
                "province_code": "12",
                "province_name": "ភ្នំពេញ",
                "district_code": "1201",
                "district_name": "ដូនពេញ",
                "commune_code": "120101",
                "commune_name": "ផ្សារកណ្ដាល",
            },
            "pickup_stop": {
                "id": 101,
                "source": "catalog",
                "label": "ផ្សារកំពង់ធំ",
                "landmark_note": "ច្រកខាងមុខផ្សារ",
                "latitude": 12.71123,
                "longitude": 104.88991,
                "commune_code": "060101",
                "commune_name": "ស្ទឹងសែន",
                "district_code": "0601",
                "district_name": "ស្ទឹងសែន",
                "province_code": "06",
                "province_name": "កំពង់ធំ",
            },
            "dropoff_stop": {
                "source": "manual_pin",
                "label": "មុខរបងវត្ត",
                "landmark_note": "មុខរបងវត្ត",
                "latitude": 11.57321,
                "longitude": 104.92111,
                "commune_code": "120101",
                "commune_name": "ផ្សារកណ្ដាល",
                "district_code": "1201",
                "district_name": "ដូនពេញ",
                "province_code": "12",
                "province_name": "ភ្នំពេញ",
            },
        },
    )

    assert create_response.status_code == 201
    created_trip = create_response.json()
    assert created_trip["departure_route"]["commune_code"] == "060101"
    assert created_trip["destination_route"]["commune_code"] == "120101"
    assert created_trip["pickup_stop"]["source"] == "catalog"
    assert created_trip["dropoff_stop"]["source"] == "manual_pin"

    trip_id = created_trip["id"]
    update_response = client.patch(
        f"/travel/trips/{trip_id}",
        headers=_auth_headers(token),
        json={"price_per_seat": 6},
    )

    assert update_response.status_code == 200
    updated_trip = update_response.json()
    assert updated_trip["price_per_seat"] == 6.0
    assert updated_trip["departure_route"]["commune_code"] == "060101"
    assert updated_trip["pickup_stop"]["label"] == "ផ្សារកំពង់ធំ"
    assert updated_trip["dropoff_stop"]["label"] == "មុខរបងវត្ត"

    get_response = client.get(f"/travel/trips/{trip_id}")

    assert get_response.status_code == 200
    fetched_trip = get_response.json()
    assert fetched_trip["departure_route"]["province_code"] == "06"
    assert fetched_trip["destination_route"]["province_code"] == "12"
    assert fetched_trip["pickup_stop"]["id"] == 101
    assert fetched_trip["dropoff_stop"]["source"] == "manual_pin"


def test_create_trip_rejects_stop_commune_mismatch() -> None:
    token = _signup_driver()
    vehicle_id = _create_vehicle(token)

    response = client.post(
        "/travel/trips",
        headers=_auth_headers(token),
        json={
            "vehicle_id": vehicle_id,
            "departure_province": "Kampong Thom",
            "destination_province": "Phnom Penh",
            "departure_time": "2026-06-06T07:30:00",
            "price_per_seat": 5,
            "total_seats": 15,
            "available_seats": 15,
            "status": "scheduled",
            "departure_route": {
                "province_code": "06",
                "province_name": "កំពង់ធំ",
                "district_code": "0601",
                "district_name": "ស្ទឹងសែន",
                "commune_code": "060101",
                "commune_name": "ស្ទឹងសែន",
            },
            "pickup_stop": {
                "source": "catalog",
                "label": "ផ្សារកំពង់ធំ",
                "latitude": 12.71123,
                "longitude": 104.88991,
                "commune_code": "999999",
                "commune_name": "Wrong Commune",
            },
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "pickup_stop.commune_code must match departure_route.commune_code"
