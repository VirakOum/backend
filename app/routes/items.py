from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import ItemCreate, ItemRead, ItemUpdate
from ..services import ItemNotFoundError, item_service

router = APIRouter(prefix="/items", tags=["items"])


@router.get("", response_model=list[ItemRead])
def list_items(db: Session = Depends(get_db)) -> list[ItemRead]:
    return item_service.list_items(db)


@router.get("/{item_id}", response_model=ItemRead)
def get_item(item_id: int, db: Session = Depends(get_db)) -> ItemRead:
    try:
        return item_service.get_item(db, item_id)
    except ItemNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Item not found") from exc


@router.post("", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def create_item(item: ItemCreate, db: Session = Depends(get_db)) -> ItemRead:
    return item_service.create_item(db, item)


@router.put("/{item_id}", response_model=ItemRead)
def update_item(item_id: int, item: ItemUpdate, db: Session = Depends(get_db)) -> ItemRead:
    try:
        return item_service.update_item(db, item_id, item)
    except ItemNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Item not found") from exc


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)) -> None:
    try:
        item_service.delete_item(db, item_id)
    except ItemNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Item not found") from exc