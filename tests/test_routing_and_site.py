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

def test_admin_static_assets_resolution():
    css_res = client.get("/admin/css/styles.css?v=1.4")
    assert css_res.status_code == 200

    logo_res = client.get("/admin/assets/logo.png")
    assert logo_res.status_code == 200

    js_res = client.get("/admin/js/app.js?v=1.4")
    assert js_res.status_code == 200

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

