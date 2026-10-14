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
