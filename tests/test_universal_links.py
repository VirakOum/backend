import json
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
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

import pytest
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

@pytest.fixture(autouse=True)
def setup_test_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)
    yield

client = TestClient(app)


def test_apple_app_site_association():
    response = client.get("/.well-known/apple-app-site-association")
    assert response.status_code == 200
    data = response.json()
    assert "applinks" in data
    assert "details" in data["applinks"]
    assert data["applinks"]["details"][0]["appID"] == "3VMD59LYS6.com.kh.mytravel.app"
    assert "/trips/*" in data["applinks"]["details"][0]["paths"]
    assert "/news/*" in data["applinks"]["details"][0]["paths"]
    assert "/ads/*" in data["applinks"]["details"][0]["paths"]

    # Also test without .well-known
    resp_alias = client.get("/apple-app-site-association")
    assert resp_alias.status_code == 200
    assert resp_alias.json() == data


def test_assetlinks_json():
    response = client.get("/.well-known/assetlinks.json")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    target = data[0]["target"]
    assert target["package_name"] == "com.kh.mytravel.mytravel"
    assert len(target["sha256_cert_fingerprints"]) >= 1

    # Also test without .well-known
    resp_alias = client.get("/assetlinks.json")
    assert resp_alias.status_code == 200
    assert resp_alias.json() == data


def test_trip_universal_link_not_found():
    fake_id = str(uuid.uuid4())
    response = client.get(f"/trips/{fake_id}", headers={"Accept": "text/html"})
    assert response.status_code == 200
    assert "My Travel" in response.text
    assert f"mytravel://trip/{fake_id}" in response.text


def test_news_universal_link_not_found():
    fake_id = str(uuid.uuid4())
    response = client.get(f"/news/{fake_id}", headers={"Accept": "text/html"})
    assert response.status_code == 200
    assert "My Travel" in response.text
    assert f"mytravel://news/{fake_id}" in response.text


def test_ads_universal_link_fallback():
    fake_id = str(uuid.uuid4())
    response = client.get(f"/ads/{fake_id}", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "https://mytravel.taxi/"


def test_admin_universal_links_get_and_update():
    # 1. GET initial configuration
    get_res = client.get("/v1/api/travel/admin/universal-links")
    assert get_res.status_code == 200
    cfg = get_res.json()
    assert cfg["apple_team_id"] == "3VMD59LYS6"
    assert cfg["apple_bundle_id"] == "com.kh.mytravel.app"
    assert cfg["apple_app_id"] == "3VMD59LYS6.com.kh.mytravel.app"
    assert cfg["android_package_name"] == "com.kh.mytravel.mytravel"
    assert len(cfg["android_sha256_fingerprints"]) >= 3
    assert "verification_urls" in cfg

    # 2. UPDATE with additional fingerprint
    custom_fp = "AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99"
    new_fps = list(cfg["android_sha256_fingerprints"]) + [
        {"fingerprint": custom_fp, "label": "QA Team Test Key", "type": "debug"}
    ]
    update_payload = {
        "apple_team_id": "3VMD59LYS6",
        "apple_bundle_id": "com.kh.mytravel.app",
        "apple_paths": ["/trips/*", "/news/*", "/ads/*", "/custom/*"],
        "webcredentials_enabled": True,
        "android_package_name": "com.kh.mytravel.mytravel",
        "android_sha256_fingerprints": new_fps,
        "primary_domain": "mytravel.taxi",
        "custom_scheme": "mytravel://",
        "fallback_url": "https://mytravel.taxi/",
        "is_active": True,
    }
    update_res = client.post("/v1/api/travel/admin/universal-links", json=update_payload)
    assert update_res.status_code == 200
    updated_cfg = update_res.json()
    assert any(f["fingerprint"] == custom_fp for f in updated_cfg["android_sha256_fingerprints"])
    assert "/custom/*" in updated_cfg["apple_paths"]

    # 3. Verify /.well-known endpoints dynamically reflect updated config
    asset_res = client.get("/.well-known/assetlinks.json")
    assert asset_res.status_code == 200
    asset_data = asset_res.json()
    assert custom_fp in asset_data[0]["target"]["sha256_cert_fingerprints"]

    aasa_res = client.get("/.well-known/apple-app-site-association")
    assert aasa_res.status_code == 200
    aasa_data = aasa_res.json()
    assert "/custom/*" in aasa_data["applinks"]["details"][0]["paths"]

    # 4. Test universal link test generator endpoint
    test_req = {
        "target_type": "trip",
        "target_id_or_path": str(uuid.uuid4()),
    }
    test_res = client.post("/v1/api/travel/admin/universal-links/test", json=test_req)
    assert test_res.status_code == 200
    test_data = test_res.json()
    assert "universal_link" in test_data
    assert "https://mytravel.taxi/trips/" in test_data["universal_link"]
    assert "mytravel://trip/" in test_data["app_deep_link"]
    assert "share_text" in test_data

    # 5. Reset to defaults
    reset_res = client.post("/v1/api/travel/admin/universal-links/reset")
    assert reset_res.status_code == 200

