import os

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse
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

root_path = os.getenv("FASTAPI_ROOT_PATH", "")

app = FastAPI(
    title="Learning FastAPI",
    version="0.1.0",
    description="A small FastAPI starter for learning how to build APIs.",
    root_path=root_path,
    docs_url="/v1/api/docs",
    redoc_url="/v1/api/redoc",
    openapi_url="/v1/api/openapi.json",
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

for r in [meta_router, travel_router, passenger_router, addresses_router, driver_fee_router, admin_router, live_ws_router]:
    app.include_router(r)
    api_v1_router.include_router(r)

app.include_router(api_v1_router)

@app.get("/", include_in_schema=False)
def serve_public_site():
    return FileResponse("app/static/site/index.html")

@app.get("/admin", include_in_schema=False)
@app.get("/admin/", include_in_schema=False)
@app.get("/admin/mytravel", include_in_schema=False)
def redirect_admin():
    return RedirectResponse(url="/admin/mytravel/", status_code=307)

app.mount("/admin/mytravel", NoCacheStaticFiles(directory="app/static/admin", html=True), name="admin")
app.mount("/css", NoCacheStaticFiles(directory="app/static/site/css"), name="site_css")
app.mount("/js", NoCacheStaticFiles(directory="app/static/site/js"), name="site_js")

