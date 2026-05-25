from fastapi import FastAPI

from .routes.items import router as items_router
from .routes.meta import router as meta_router
from .routes.travel import router as travel_router
from .routes.passenger import router as passenger_router

app = FastAPI(
    title="Learning FastAPI",
    version="0.1.0",
    description="A small FastAPI starter for learning how to build APIs.",
    servers=[
        {
            "url": "http://127.0.0.1:8000",
            "description": "Local development server",
        }
    ],
)

# app.include_router(meta_router)
# app.include_router(items_router)
app.include_router(travel_router)
app.include_router(passenger_router)
