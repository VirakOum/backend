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
    root_response = client.get("/")
    health_response = client.get("/health")

    assert root_response.status_code == 200
    assert root_response.json()["message"] == "FastAPI project is ready"
    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}


def test_item_crud_flow() -> None:
    create_response = client.post(
        "/items",
        json={"name": "Notebook", "description": "A place for notes"},
    )

    assert create_response.status_code == 201
    created_item = create_response.json()
    assert created_item["id"] == 1
    assert created_item["name"] == "Notebook"

    list_response = client.get("/items")
    assert list_response.status_code == 200
    assert list_response.json() == [created_item]

    detail_response = client.get("/items/1")
    assert detail_response.status_code == 200
    assert detail_response.json() == created_item

    update_response = client.put(
        "/items/1",
        json={"name": "Updated notebook", "description": "Revised notes"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Updated notebook"

    delete_response = client.delete("/items/1")
    assert delete_response.status_code == 204

    missing_response = client.get("/items/1")
    assert missing_response.status_code == 404
    assert missing_response.json()["detail"] == "Item not found"