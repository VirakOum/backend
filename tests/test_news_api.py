import json
from datetime import datetime, timedelta
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


def test_news_crud_and_public_feed():
    # 1. Post a new article
    payload = {
        "title": "Breaking News: Phnom Penh Highway Open",
        "title_kh": "ព័ត៌មានទាន់ហេតុការណ៍: ផ្លូវល្បឿនលឿនភ្នំពេញបើកដំណើរការ",
        "summary": "Expressway opens for weekend commuters.",
        "summary_kh": "ផ្លូវល្បឿនលឿនបើកឱ្យដំណើរការសម្រាប់អ្នកធ្វើដំណើរចុងសប្តាហ៍។",
        "content": "Full article details...",
        "image_url": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957",
        "source_url": "https://m.freshnews.com.kh/123",
        "source_name": "Fresh News",
        "category": "Breaking News",
        "is_breaking": True,
        "is_active": True,
    }
    resp = client.post("/v1/api/travel/admin/news", json=payload)
    assert resp.status_code == 201, resp.text
    created = resp.json()
    assert created["title"] == payload["title"]
    assert created["source_name"] == "Fresh News"
    assert created["is_breaking"] is True
    article_id = created["id"]

    # 2. List in admin
    resp = client.get("/v1/api/travel/admin/news")
    assert resp.status_code == 200
    articles = resp.json()
    assert any(a["id"] == article_id for a in articles)

    # 3. Read in public travel feed
    resp = client.get("/v1/api/travel/news")
    assert resp.status_code == 200
    feed = resp.json()
    assert "articles" in feed
    assert any(a["id"] == article_id for a in feed["articles"])

    # 4. Toggle active status
    resp = client.post(f"/v1/api/travel/admin/news/{article_id}/toggle-active")
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False

    # 5. Inactive article should not appear in public feed
    resp = client.get("/v1/api/travel/news")
    assert resp.status_code == 200
    feed = resp.json()
    assert not any(a["id"] == article_id for a in feed["articles"])

    # 6. Delete article
    resp = client.delete(f"/v1/api/travel/admin/news/{article_id}")
    assert resp.status_code == 204
