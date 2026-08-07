import json
from datetime import datetime, timedelta
from pathlib import Path
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


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _signup_passenger(phone: str = "098765432") -> str:
    response = client.post(
        "/travel/auth/signup",
        json={
            "phone": phone,
            "full_name": "Passenger Demo",
            "role": "passenger",
            "password": "strongpass123",
            "avatar_url": None,
        },
    )
    assert response.status_code == 201
    return response.json()["token"]


def setup_function() -> None:
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)


def test_discounts_crud_flow() -> None:
    token = _signup_passenger()
    # 1. Create a discount
    payload = {
        "code": "PROMO20",
        "title": "20% off all trips",
        "title_kh": "បញ្ចុះតម្លៃ ២០%",
        "discount_percent": 20,
        "description": "20% off promotion",
        "description_kh": "ប្រូម៉ូសិនពិសេស",
        "expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
        "is_active": True
    }
    response = client.post("/travel/admin/discounts", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["code"] == "PROMO20"
    assert data["discount_percent"] == 20
    assert data["is_active"] is True
    discount_id = data["id"]

    # 2. List discounts (admin)
    list_response = client.get("/travel/admin/discounts")
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert len(list_data) == 1
    assert list_data[0]["id"] == discount_id

    # 3. Update discount
    update_payload = {
        "code": "PROMO25",
        "title": "25% off all trips",
        "title_kh": "បញ្ចុះតម្លៃ ២៥%",
        "discount_percent": 25,
        "description": "25% off promotion",
        "description_kh": "ប្រូម៉ូសិនពិសេស ២៥%",
        "expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
        "is_active": True
    }
    update_response = client.put(f"/travel/admin/discounts/{discount_id}", json=update_payload)
    assert update_response.status_code == 200
    updated_data = update_response.json()
    assert updated_data["code"] == "PROMO25"
    assert updated_data["discount_percent"] == 25

    # 4. Toggle active status
    toggle_response = client.post(f"/travel/admin/discounts/{discount_id}/toggle-active")
    assert toggle_response.status_code == 200
    toggled_data = toggle_response.json()
    assert toggled_data["is_active"] is False

    # 5. Fetch active discounts (passenger side)
    # Toggled off so it should be empty
    passenger_response = client.get("/passenger/discounts", headers=_auth_headers(token))
    assert passenger_response.status_code == 200
    passenger_data = passenger_response.json()
    assert len(passenger_data) == 0

    # Toggle active status back to true
    client.post(f"/travel/admin/discounts/{discount_id}/toggle-active")
    passenger_response = client.get("/passenger/discounts", headers=_auth_headers(token))
    assert passenger_response.status_code == 200
    passenger_data = passenger_response.json()
    assert len(passenger_data) == 1
    assert passenger_data[0]["code"] == "PROMO25"

    # 6. Delete discount
    delete_response = client.delete(f"/travel/admin/discounts/{discount_id}")
    assert delete_response.status_code == 204

    # Verify not found in admin list
    list_response = client.get("/travel/admin/discounts")
    assert len(list_response.json()) == 0


def test_ads_crud_flow() -> None:
    token = _signup_passenger("098765431")
    # 1. Create an ad banner
    payload = {
        "title": "Welcome Ad",
        "title_kh": "ពាណិជ្ជកម្មស្វាគមន៍",
        "image_url": "https://example.com/ad.jpg",
        "link_url": "https://example.com",
        "description": "Welcome promotion banner",
        "description_kh": "ផ្ទាំងផ្សព្វផ្សាយស្វាគមន៍",
        "is_active": True
    }
    response = client.post("/travel/admin/ads", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["title"] == "Welcome Ad"
    assert data["image_url"] == "https://example.com/ad.jpg"
    assert data["is_active"] is True
    ad_id = data["id"]

    # 2. List ads (admin)
    list_response = client.get("/travel/admin/ads")
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert len(list_data) == 1
    assert list_data[0]["id"] == ad_id

    # 3. Update ad
    update_payload = {
        "title": "Welcome Ad V2",
        "title_kh": "ពាណិជ្ជកម្មស្វាគមន៍ ថ្មី",
        "image_url": "https://example.com/ad2.jpg",
        "link_url": "https://example.com/v2",
        "description": "Updated promotion banner",
        "description_kh": "ផ្ទាំងផ្សព្វផ្សាយថ្មី",
        "is_active": True
    }
    update_response = client.put(f"/travel/admin/ads/{ad_id}", json=update_payload)
    assert update_response.status_code == 200
    updated_data = update_response.json()
    assert updated_data["title"] == "Welcome Ad V2"
    assert updated_data["image_url"] == "https://example.com/ad2.jpg"

    # 4. Toggle active status
    toggle_response = client.post(f"/travel/admin/ads/{ad_id}/toggle-active")
    assert toggle_response.status_code == 200
    toggled_data = toggle_response.json()
    assert toggled_data["is_active"] is False

    # 5. Fetch active ads (passenger side)
    # Toggled off so it should be empty
    passenger_response = client.get("/passenger/ads", headers=_auth_headers(token))
    assert passenger_response.status_code == 200
    passenger_data = passenger_response.json()
    assert len(passenger_data) == 0

    # Toggle active status back to true
    client.post(f"/travel/admin/ads/{ad_id}/toggle-active")
    passenger_response = client.get("/passenger/ads", headers=_auth_headers(token))
    assert passenger_response.status_code == 200
    passenger_data = passenger_response.json()
    assert len(passenger_data) == 1
    assert passenger_data[0]["title"] == "Welcome Ad V2"

    # 6. Delete ad
    delete_response = client.delete(f"/travel/admin/ads/{ad_id}")
    assert delete_response.status_code == 204

    # Verify not found in admin list
    list_response = client.get("/travel/admin/ads")
    assert len(list_response.json()) == 0


def test_admin_ad_image_upload_from_device_file() -> None:
    image_bytes = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00"
        b"\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x01\x01\x01\x00"
        b"\x18\xdd\x8d\xb0"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    response = client.post(
        "/travel/admin/ads/upload-image",
        content=image_bytes,
        headers={"Content-Type": "image/png"},
    )

    assert response.status_code == 200, response.text
    image_url = response.json()["image_url"]
    assert image_url.startswith("/admin/assets/uploads/banner-ads/")
    assert image_url.endswith(".png")

    saved_path = Path("app/static/admin") / image_url.removeprefix("/admin/")
    try:
        assert saved_path.exists()
        assert saved_path.read_bytes() == image_bytes
    finally:
        saved_path.unlink(missing_ok=True)


def test_admin_ad_image_upload_rejects_non_image() -> None:
    response = client.post(
        "/travel/admin/ads/upload-image",
        content=b"not an image",
        headers={"Content-Type": "text/plain"},
    )

    assert response.status_code == 400
