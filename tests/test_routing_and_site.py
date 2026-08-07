import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_public_site_serves_landing_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "MyTravel Taxi & Inter-City Travel | Cambodia" in response.text
    assert "MYTRAVEL.TAXI" in response.text

def test_admin_redirect_to_mytravel():
    response = client.get("/admin", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/admin/mytravel/"

def test_admin_mytravel_dashboard():
    response = client.get("/admin/mytravel/")
    assert response.status_code == 200
    assert "My Travel - Command Dashboard" in response.text

def test_v1_api_and_direct_api_endpoints():
    response_v1_root = client.get("/v1/api")
    assert response_v1_root.status_code == 200
    assert response_v1_root.json()["message"] == "FastAPI project is ready"

    response_v1 = client.get("/v1/api/health")
    assert response_v1.status_code == 200
    assert response_v1.json() == {"status": "ok"}

    response_direct = client.get("/health")
    assert response_direct.status_code == 200
    assert response_direct.json() == {"status": "ok"}
