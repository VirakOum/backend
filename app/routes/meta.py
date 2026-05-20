from fastapi import APIRouter

router = APIRouter(tags=["meta"])


@router.get("/")
def root() -> dict[str, str]:
    return {"message": "FastAPI project is ready", "docs": "/docs", "redoc": "/redoc"}


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}