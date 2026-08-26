import json
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
from app.models import VehicleModel

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
client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)


def test_vehicle_models_admin_and_public_crud():
    # 1. Initially empty list
    response = client.get("/v1/api/travel/admin/vehicle-models")
    assert response.status_code == 200
    assert response.json() == []

    # 2. Create vehicle model
    create_payload = {
        "brand": "Toyota",
        "model_name": "Prius",
        "display_name": "Toyota Prius 2024",
        "vehicle_type": "Sedan",
        "seat_count": 4,
        "is_active": True,
        "sort_order": 1,
    }
    create_res = client.post("/v1/api/travel/admin/vehicle-models", json=create_payload)
    assert create_res.status_code == 201
    model_data = create_res.json()
    model_id = model_data["id"]
    assert model_data["brand"] == "Toyota"
    assert model_data["model_name"] == "Prius"
    assert model_data["display_name"] == "Toyota Prius 2024"
    assert model_data["seat_count"] == 4

    # 3. Create second model
    client.post(
        "/v1/api/travel/admin/vehicle-models",
        json={
            "brand": "Hyundai",
            "model_name": "Starex",
            "vehicle_type": "Minivan",
            "seat_count": 12,
            "is_active": True,
            "sort_order": 2,
        },
    )

    # 4. List models via Admin API with filter
    list_res = client.get("/v1/api/travel/admin/vehicle-models?query=prius")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1
    assert list_res.json()[0]["brand"] == "Toyota"

    # 5. List models via Public API (GET /v1/api/travel/vehicle-models)
    public_res = client.get("/v1/api/travel/vehicle-models")
    assert public_res.status_code == 200
    assert len(public_res.json()) == 2

    # 6. Update vehicle model
    update_res = client.put(
        f"/v1/api/travel/admin/vehicle-models/{model_id}",
        json={"display_name": "Toyota Prius Hybrid", "seat_count": 5},
    )
    assert update_res.status_code == 200
    assert update_res.json()["display_name"] == "Toyota Prius Hybrid"
    assert update_res.json()["seat_count"] == 5

    # 7. Toggle active status
    toggle_res = client.post(f"/v1/api/travel/admin/vehicle-models/{model_id}/toggle-active")
    assert toggle_res.status_code == 200
    assert toggle_res.json()["is_active"] is False

    # 8. Public API should now return only 1 active model (Hyundai Starex)
    public_active_res = client.get("/v1/api/travel/vehicle-models")
    assert public_active_res.status_code == 200
    assert len(public_active_res.json()) == 1
    assert public_active_res.json()[0]["brand"] == "Hyundai"

    # 9. Delete vehicle model
    del_res = client.delete(f"/v1/api/travel/admin/vehicle-models/{model_id}")
    assert del_res.status_code == 204

    # 10. Admin list has only 1 model left
    admin_after_del = client.get("/v1/api/travel/admin/vehicle-models")
    assert admin_after_del.status_code == 200
    assert len(admin_after_del.json()) == 1
