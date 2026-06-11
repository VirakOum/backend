from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.items import router as items_router
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
            "url": "http://192.168.1.153:8000",
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

# app.include_router(meta_router)
# app.include_router(items_router)
app.include_router(travel_router)
app.include_router(passenger_router)
app.include_router(addresses_router)
app.include_router(driver_fee_router)
