from fastapi import APIRouter

router = APIRouter(tags=["meta"])


@router.get("/meta")
def root() -> dict[str, str]:
    return {"message": "FastAPI project is ready", "docs": "/v1/api/docs", "redoc": "/v1/api/redoc"}


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}