import json
import pytest
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
from app.models import AppVersionConfig
from app.version_control import parse_semver, evaluate_version

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


app.dependency_overrides[get_db] = override_get_db
Base.metadata.create_all(bind=test_engine)
client = TestClient(app)


def test_parse_semver():
    assert parse_semver("1.0.0") == (1, 0, 0)
    assert parse_semver("v1.2.3") == (1, 2, 3)
    assert parse_semver("1.2") == (1, 2, 0)
    assert parse_semver("1.0.0+7") == (1, 0, 0)
    assert parse_semver("2.0.1-beta") == (2, 0, 1)
    assert parse_semver(None) == (0, 0, 0)


def test_evaluate_version_rules():
    # 1. Force update: current < min
    action, reason = evaluate_version(
        current_version="1.0.0",
        min_version="1.0.5",
        latest_version="1.1.0",
    )
    assert action == "force_update"

    # 2. Optional update: min <= current < latest
    action, reason = evaluate_version(
        current_version="1.0.5",
        min_version="1.0.5",
        latest_version="1.1.0",
    )
    assert action == "optional_update"

    action, reason = evaluate_version(
        current_version="1.0.8",
        min_version="1.0.5",
        latest_version="1.1.0",
    )
    assert action == "optional_update"

    # 3. Continue: current >= latest
    action, reason = evaluate_version(
        current_version="1.1.0",
        min_version="1.0.5",
        latest_version="1.1.0",
    )
    assert action == "continue"

    action, reason = evaluate_version(
        current_version="1.2.0",
        min_version="1.0.5",
        latest_version="1.1.0",
    )
    assert action == "continue"

    # 4. Enforce update flag: min <= current < latest, but force_update is True
    action, reason = evaluate_version(
        current_version="1.0.8",
        min_version="1.0.5",
        latest_version="1.1.0",
        force_update_flag=True,
    )
    assert action == "force_update"


def test_public_version_check_endpoint():
    # Set known config
    response = client.post(
        "/v1/api/travel/admin/app-versions",
        json={
            "platform": "android",
            "latest_version": "1.1.0",
            "min_version": "1.0.5",
            "force_update": False,
            "update_url": "https://play.google.com/store/apps/details?id=com.kh.mytravel.mytravel",
            "title": "New Version Available",
            "title_km": "មានកំណែថ្មីនៃកម្មវិធី",
            "release_notes": "• Improved booking speed\n• Bug fixes",
            "release_notes_km": "• បង្កើនល្បឿននៃការកក់\n• កែសម្រួលចំណុចខ្វះខាត",
            "is_active": True,
        },
    )
    assert response.status_code == 200

    # Case A: Force update (0.9.0 < 1.0.5)
    r = client.get("/v1/api/travel/version?platform=android&current_version=0.9.0")
    assert r.status_code == 200
    data = r.json()
    assert data["latest_version"] == "1.1.0"
    assert data["min_version"] == "1.0.5"
    assert data["action"] == "force_update"

    # Also test /api/version alias
    r_alias = client.get("/api/version?platform=android&current_version=0.9.0")
    assert r_alias.status_code == 200
    assert r_alias.json()["action"] == "force_update"

    # Case B: Optional update (1.0.6 between 1.0.5 and 1.1.0)
    r = client.get("/v1/api/travel/version?platform=android&current_version=1.0.6")
    assert r.status_code == 200
    assert r.json()["action"] == "optional_update"

    # Case C: Continue (1.1.0 >= 1.1.0)
    r = client.get("/v1/api/travel/version?platform=android&current_version=1.1.0")
    assert r.status_code == 200
    assert r.json()["action"] == "continue"


def test_admin_app_versions_crud_and_simulation():
    # 1. List app versions
    r = client.get("/v1/api/travel/admin/app-versions")
    assert r.status_code == 200
    platforms = [item["platform"] for item in r.json()]
    assert "android" in platforms
    assert "ios" in platforms

    # 2. Update iOS config
    r = client.post(
        "/v1/api/travel/admin/app-versions",
        json={
            "platform": "ios",
            "latest_version": "2.0.0",
            "min_version": "1.5.0",
            "force_update": True,
            "update_url": "https://apps.apple.com/app/mytravel/id123456",
            "title": "Major iOS Update",
            "title_km": "បច្ចុប្បន្នភាពធំសម្រាប់ iOS",
            "release_notes": "Complete redesign",
            "release_notes_km": "ការផ្លាស់ប្តូររូបរាងថ្មី",
            "is_active": True,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["latest_version"] == "2.0.0"
    assert data["min_version"] == "1.5.0"
    assert data["force_update"] is True

    # 3. Simulate version logic
    r_sim = client.post(
        "/v1/api/travel/admin/app-versions/simulate",
        json={"platform": "ios", "current_version": "1.4.0"},
    )
    assert r_sim.status_code == 200
    assert r_sim.json()["action"] == "force_update"

    r_sim2 = client.post(
        "/v1/api/travel/admin/app-versions/simulate",
        json={"platform": "ios", "current_version": "2.0.0"},
    )
    assert r_sim2.status_code == 200
    assert r_sim2.json()["action"] == "continue"
