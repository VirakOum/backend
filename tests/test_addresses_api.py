from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db import get_db
from app.models import Address, AddressFormEntry


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
Address.__table__.create(bind=test_engine)
AddressFormEntry.__table__.create(bind=test_engine)

client = TestClient(app)


def setup_function() -> None:
    app.dependency_overrides[get_db] = override_get_db
    AddressFormEntry.__table__.drop(bind=test_engine, checkfirst=True)
    Address.__table__.drop(bind=test_engine, checkfirst=True)
    Address.__table__.create(bind=test_engine)
    AddressFormEntry.__table__.create(bind=test_engine)

    db = TestingSessionLocal()
    try:
        db.add_all(
            [
                Address(id=1, code="855", name="Cambodia", description="កម្ពុជា", type="country"),
                Address(
                    id=2,
                    code="06",
                    name="Kampong Thom Province",
                    description="កំពង់ធំ",
                    type="province",
                    parent_code="855",
                ),
                Address(
                    id=3,
                    code="601",
                    name="Stueng Saen",
                    description="ស្ទឹងសែន",
                    type="district",
                    parent_code="06",
                ),
                Address(
                    id=4,
                    code="60101",
                    name="Kampong Roteh",
                    description="កំពង់រទេះ",
                    type="commune",
                    parent_code="601",
                ),
                Address(
                    id=5,
                    code="6010101",
                    name="Village A",
                    description="ភូមិ A",
                    type="village",
                    parent_code="60101",
                    reference="Near pagoda gate",
                    latitude=12.345678,
                    longitude=104.987654,
                ),
                Address(
                    id=6,
                    code="60102",
                    name="Prek Same",
                    description="ព្រែកសាម",
                    type="commune",
                    parent_code="601",
                ),
            ]
        )
        db.commit()
    finally:
        db.close()


def test_get_provinces() -> None:
    response = client.get("/v1/api/addresses/provinces")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["code"] == "06"
    assert body[0]["description"] == "កំពង់ធំ"


def test_cascading_address_dropdown_routes() -> None:
    districts_response = client.get("/v1/api/addresses/districts/06")
    communes_response = client.get("/v1/api/addresses/communes/601")
    villages_response = client.get("/v1/api/addresses/villages/60101")

    assert districts_response.status_code == 200
    assert districts_response.json()[0]["description"] == "ស្ទឹងសែន"

    assert communes_response.status_code == 200
    assert communes_response.json()[0]["code"] == "60101"

    assert villages_response.status_code == 200
    assert villages_response.json()[0]["parent_code"] == "60101"


def test_generic_address_lookup_routes() -> None:
    by_type_response = client.get("/v1/api/addresses/by-type/district")
    by_parent_response = client.get("/v1/api/addresses/by-parent/06")
    by_code_response = client.get("/v1/api/addresses/code/601")

    assert by_type_response.status_code == 200
    assert by_type_response.json()[0]["code"] == "601"

    assert by_parent_response.status_code == 200
    assert by_parent_response.json()[0]["type"] == "district"

    assert by_code_response.status_code == 200
    assert by_code_response.json()["description"] == "ស្ទឹងសែន"


def test_districts_route_rejects_non_province_code() -> None:
    response = client.get("/v1/api/addresses/districts/601")

    assert response.status_code == 400
    assert response.json()["detail"] == "province_code must belong to a province"


def test_create_address_form_entry() -> None:
    response = client.post(
        "/v1/api/addresses/forms",
        json={
            "province_code": "06",
            "district_code": "601",
            "commune_code": "60101",
            "village_code": "6010101",
            "detail_line": "House 12",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["province_code"] == "06"
    assert body["district_code"] == "601"
    assert body["commune_code"] == "60101"
    assert body["village_code"] == "6010101"
    assert body["formatted_address_en"] == "House 12, Village A, Kampong Roteh, Stueng Saen, Kampong Thom Province, Cambodia"
    assert body["formatted_address_km"] == "House 12, ភូមិ A, កំពង់រទេះ, ស្ទឹងសែន, កំពង់ធំ, កម្ពុជា"


def test_create_address_form_entry_rejects_invalid_hierarchy() -> None:
    response = client.post(
        "/v1/api/addresses/forms",
        json={
            "province_code": "06",
            "district_code": "601",
            "commune_code": "60101",
            "village_code": "601",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "village_code must belong to the selected commune"


def test_get_commune_stops_returns_catalog_stops() -> None:
    response = client.get("/v1/api/addresses/stops/communes/60101")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == 5
    assert body[0]["source"] == "catalog"
    assert body[0]["label"] == "ភូមិ A"
    assert body[0]["landmark_note"] == "Near pagoda gate"
    assert body[0]["latitude"] == 12.345678
    assert body[0]["longitude"] == 104.987654
    assert body[0]["commune_code"] == "60101"
    assert body[0]["district_code"] == "601"
    assert body[0]["province_code"] == "06"


def test_get_commune_stops_returns_empty_list_when_no_catalog_stops_exist() -> None:
    response = client.get("/v1/api/addresses/stops/communes/60102")

    assert response.status_code == 200
    assert response.json() == []


def test_resolve_stop_by_coordinates() -> None:
    response = client.post(
        "/v1/api/addresses/resolve-stop",
        json={
            "latitude": 12.345,
            "longitude": 104.987,
            "google_label": "Central Market",
            "google_landmark_note": "Near station",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["province"]["code"] == "06"
    assert body["province"]["name"] == "Kampong Thom Province"
    assert body["district"]["code"] == "601"
    assert body["commune"]["code"] == "60101"
    assert body["stop"]["label"] == "ភូមិ A"
    assert body["stop"]["commune_code"] == "60101"
    assert body["stop"]["district_code"] == "601"
    assert body["stop"]["province_code"] == "06"

