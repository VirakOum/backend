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
                ),
            ]
        )
        db.commit()
    finally:
        db.close()


def test_get_provinces() -> None:
    response = client.get("/addresses/provinces")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["code"] == "06"
    assert body[0]["description"] == "កំពង់ធំ"


def test_cascading_address_dropdown_routes() -> None:
    districts_response = client.get("/addresses/districts/06")
    communes_response = client.get("/addresses/communes/601")
    villages_response = client.get("/addresses/villages/60101")

    assert districts_response.status_code == 200
    assert districts_response.json()[0]["description"] == "ស្ទឹងសែន"

    assert communes_response.status_code == 200
    assert communes_response.json()[0]["code"] == "60101"

    assert villages_response.status_code == 200
    assert villages_response.json()[0]["parent_code"] == "60101"


def test_generic_address_lookup_routes() -> None:
    by_type_response = client.get("/addresses/by-type/district")
    by_parent_response = client.get("/addresses/by-parent/06")
    by_code_response = client.get("/addresses/code/601")

    assert by_type_response.status_code == 200
    assert by_type_response.json()[0]["code"] == "601"

    assert by_parent_response.status_code == 200
    assert by_parent_response.json()[0]["type"] == "district"

    assert by_code_response.status_code == 200
    assert by_code_response.json()["description"] == "ស្ទឹងសែន"


def test_districts_route_rejects_non_province_code() -> None:
    response = client.get("/addresses/districts/601")

    assert response.status_code == 400
    assert response.json()["detail"] == "province_code must belong to a province"


def test_create_address_form_entry() -> None:
    response = client.post(
        "/addresses/forms",
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
        "/addresses/forms",
        json={
            "province_code": "06",
            "district_code": "601",
            "commune_code": "60101",
            "village_code": "601",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "village_code must belong to the selected commune"
