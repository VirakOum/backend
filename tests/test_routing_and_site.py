import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_public_site_serves_landing_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "MyTravel Taxi & Inter-City Travel | Cambodia" in response.text
    assert "MYTRAVEL.TAXI" in response.text

def test_privacy_policy_page():
    for path in ["/privacy", "/privacy.html", "/v1/api/privacy", "/v1/api/privacy.html"]:
        res = client.get(path)
        assert res.status_code == 200, f"Failed for path {path}"
        assert "My Travel Privacy Policy" in res.text
        assert "account-deletion" in res.text

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


def test_both_prefixed_and_unprefixed_api_routes():
    # Both unprefixed and prefixed routes should be accessible for maximum reverse-proxy compatibility
    assert client.get("/addresses/provinces").status_code == 200
    assert client.get("/travel/app-config").status_code == 200
    assert client.get("/v1/api/addresses/provinces").status_code == 200
    assert client.get("/v1/api/travel/app-config").status_code == 200


def test_openapi_schema_contains_only_v1_api_paths():
    response = client.get("/v1/api/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    paths = schema.get("paths", {})
    assert len(paths) > 0
    for path in paths:
        assert path.startswith("/v1/api"), f"Expected all API paths to start with /v1/api, found: {path}"


def test_api_docs_endpoints():
    for path in ["/api/docs", "/v1/api/docs", "/docs"]:
        res = client.get(path)
        assert res.status_code == 200, f"Failed for docs path {path}"
        assert "SwaggerUIBundle" in res.text

    for path in ["/api/openapi.json", "/v1/api/openapi.json", "/openapi.json"]:
        res = client.get(path)
        assert res.status_code == 200, f"Failed for openapi path {path}"

    redirect_res = client.get("/api", follow_redirects=False)
    assert redirect_res.status_code in (307, 302)
    assert redirect_res.headers["location"] == "/api/docs"



def test_favicon_and_assets_resolution():
    favicon_res = client.get("/favicon.ico")
    assert favicon_res.status_code == 200
    assert favicon_res.headers["content-type"] in ("image/png", "image/x-icon", "image/vnd.microsoft.icon")

    asset_res = client.get("/assets/logo.png")
    assert asset_res.status_code == 200


def test_smart_app_download_redirects():
    # iOS redirect
    ios_res = client.get("/app", headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"}, follow_redirects=False)
    assert ios_res.status_code == 302
    assert "apps.apple.com/app/my-travel/id6815109556" in ios_res.headers["location"]

    # Android redirect
    android_res = client.get("/download", headers={"User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8)"}, follow_redirects=False)
    assert android_res.status_code == 302
    assert "play.google.com/store/apps/details?id=com.kh.mytravel.mytravel" in android_res.headers["location"]

    # Desktop fallback
    desktop_res = client.get("/app", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, follow_redirects=False)
    assert desktop_res.status_code == 302
    assert desktop_res.headers["location"] == "/#download"

    # Direct APK fallback to Google Play when no local APK uploaded
    apk_res = client.get("/download/mytravel-passenger.apk", follow_redirects=False)
    assert apk_res.status_code == 302
    assert "play.google.com/store/apps/details?id=com.kh.mytravel.mytravel" in apk_res.headers["location"]



