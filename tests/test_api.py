from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db import Base, get_db

from app import models  # noqa: F401


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


def setup_function() -> None:
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)


def test_root_and_health() -> None:
    site_response = client.get("/")
    v1_api_response = client.get("/v1/api")
    health_response = client.get("/v1/api/health")

    assert site_response.status_code == 200
    assert "MYTRAVEL.TAXI" in site_response.text
    assert v1_api_response.status_code == 200
    assert v1_api_response.json()["message"] == "FastAPI project is ready"
    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}