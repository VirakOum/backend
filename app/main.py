from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from .db import engine
from .routes.meta import router as meta_router
from .routes.travel import router as travel_router
from .routes.passenger import router as passenger_router
from .routes.addresses import router as addresses_router
from .routes.driver_fee import router as driver_fee_router

app = FastAPI(
    title="Learning FastAPI",
    version="0.1.0",
    description="A small FastAPI starter for learning how to build APIs.",
    servers=[
        {
            "url": "http://192.168.1.101:8000",
            "description": "Local development server",
        }
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


# app.include_router(meta_router)
app.include_router(travel_router)
app.include_router(passenger_router)
app.include_router(addresses_router)
app.include_router(driver_fee_router)
