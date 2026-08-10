import os
from pathlib import Path

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from .db import engine
from .routes.meta import router as meta_router
from .routes.travel import router as travel_router
from .routes.passenger import router as passenger_router
from .routes.addresses import router as addresses_router
from .routes.driver_fee import router as driver_fee_router
from .routes.admin import router as admin_router
from .routes.live_ws import router as live_ws_router
from .routes.items import router as items_router

root_path = os.getenv("FASTAPI_ROOT_PATH", "")
BASE_DIR = Path(__file__).resolve().parent
STATIC_SITE_DIR = BASE_DIR / "static" / "site"
STATIC_ADMIN_DIR = BASE_DIR / "static" / "admin"

app = FastAPI(
    title="Learning FastAPI",
    version="0.1.0",
    description="A small FastAPI starter for learning how to build APIs.",
    root_path=root_path,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    servers=[
        {
            "url": "https://mytravel.taxi/v1/api",
            "description": "Production server",
        },
        {
            "url": "http://10.20.30.211:8000",
            "description": "Local development server",
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _ensure_trip_live_location_columns() -> None:
    inspector = inspect(engine)
    if not inspector.has_table("trips"):
        return

    columns = {column["name"] for column in inspector.get_columns("trips")}
    statements: list[str] = []
    if "live_lat" not in columns:
        statements.append("ALTER TABLE trips ADD COLUMN live_lat NUMERIC(10, 6)")
    if "live_lng" not in columns:
        statements.append("ALTER TABLE trips ADD COLUMN live_lng NUMERIC(10, 6)")
    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
        connection.execute(
            text(
                """
                UPDATE trips
                SET live_lat = departure_lat,
                    live_lng = departure_lng
                WHERE live_location_expires_at IS NOT NULL
                  AND (live_lat IS NULL OR live_lng IS NULL)
                """
            )
        )


@app.on_event("startup")
def _apply_runtime_trip_schema_repairs() -> None:
    _ensure_trip_live_location_columns()


class NoCacheStaticFiles(StaticFiles):
    def is_not_modified(self, response_headers, request_headers) -> bool:
        return False

    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


# Explicit API router under /v1/api
api_v1_router = APIRouter(prefix="/v1/api")

@api_v1_router.get("", include_in_schema=False)
@api_v1_router.get("/", include_in_schema=False)
def api_v1_root():
    return {"message": "FastAPI project is ready", "docs": "/v1/api/docs", "redoc": "/v1/api/redoc"}

for r in [meta_router, travel_router, passenger_router, addresses_router, driver_fee_router, admin_router, live_ws_router, items_router]:
    app.include_router(r)
    api_v1_router.include_router(r)

app.include_router(api_v1_router)

# Custom Swagger UI & OpenAPI Endpoints (supporting both /v1/api/docs and /docs)
@app.get("/v1/api/openapi.json", include_in_schema=False)
@app.get("/openapi.json", include_in_schema=False)
def custom_openapi_json():
    return JSONResponse(get_openapi(title=app.title, version=app.version, description=app.description, routes=app.routes))

@app.get("/v1/api/docs", include_in_schema=False)
@app.get("/docs", include_in_schema=False)
def custom_swagger_ui():
    return get_swagger_ui_html(
        openapi_url="/v1/api/openapi.json",
        title=app.title + " - API Docs",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )

@app.get("/v1/api/redoc", include_in_schema=False)
@app.get("/redoc", include_in_schema=False)
def custom_redoc_ui():
    return get_redoc_html(
        openapi_url="/v1/api/openapi.json",
        title=app.title + " - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
    )

# Static files and Admin Dashboard explicit route handlers
@app.get("/css/{filename:path}", include_in_schema=False)
@api_v1_router.get("/css/{filename:path}", include_in_schema=False)
def serve_css(filename: str):
    file_path = STATIC_SITE_DIR / "css" / filename
    if file_path.is_file():
        return FileResponse(file_path, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    raise HTTPException(status_code=404, detail="CSS file not found")

@app.get("/js/{filename:path}", include_in_schema=False)
@api_v1_router.get("/js/{filename:path}", include_in_schema=False)
def serve_js(filename: str):
    file_path = STATIC_SITE_DIR / "js" / filename
    if file_path.is_file():
        return FileResponse(file_path, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    raise HTTPException(status_code=404, detail="JS file not found")

@app.get("/", include_in_schema=False)
def serve_public_site():
    return FileResponse(STATIC_SITE_DIR / "index.html", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

@app.get("/admin", include_in_schema=False)
@app.get("/admin/", include_in_schema=False)
@app.get("/admin/mytravel", include_in_schema=False)
@app.get("/admin/mytravel/", include_in_schema=False)
@app.get("/admin/mytravel/{filepath:path}", include_in_schema=False)
@api_v1_router.get("/admin", include_in_schema=False)
@api_v1_router.get("/admin/", include_in_schema=False)
@api_v1_router.get("/admin/mytravel", include_in_schema=False)
@api_v1_router.get("/admin/mytravel/", include_in_schema=False)
@api_v1_router.get("/admin/mytravel/{filepath:path}", include_in_schema=False)
def serve_admin_dashboard(filepath: str = ""):
    if not filepath or filepath == "index.html":
        return FileResponse(STATIC_ADMIN_DIR / "index.html", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    target = STATIC_ADMIN_DIR / filepath
    if target.is_file():
        return FileResponse(target, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    return FileResponse(STATIC_ADMIN_DIR / "index.html", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

