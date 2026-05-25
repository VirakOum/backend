from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db import get_db
from ..models import PassengerQuickPlace, User
from ..schemas import (
    PassengerPlaceItem,
    PassengerPlacesResponse,
    PassengerPlaceUpsert,
    ScheduleOption,
    TripSearchConfigResponse,
)

router = APIRouter(prefix="/passenger", tags=["passenger"])

DEFAULT_PLACE_LABELS = {
    "home": "Home",
    "work": "Work",
}


@router.get("/profile/places", response_model=PassengerPlacesResponse)
def get_profile_places(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PassengerPlacesResponse:
    if current_user.role != "passenger":
        raise HTTPException(status_code=403, detail="Only passengers can access quick places")

    rows = db.execute(
        select(PassengerQuickPlace).where(PassengerQuickPlace.user_id == current_user.id)
    ).scalars().all()
    row_by_key = {row.key: row for row in rows}

    places: list[PassengerPlaceItem] = []
    for key, label in DEFAULT_PLACE_LABELS.items():
        row = row_by_key.get(key)
        places.append(
            PassengerPlaceItem(
                key=key,
                label=label,
                address_id=str(row.id) if row else None,
                address_line=row.address_line if row else None,
                has_address=row is not None,
            )
        )

    return PassengerPlacesResponse(places=places)


@router.put("/profile/places/{key}", response_model=PassengerPlaceItem)
def upsert_profile_place(
    payload: PassengerPlaceUpsert,
    key: str = Path(pattern="^[a-z_]{2,20}$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PassengerPlaceItem:
    if current_user.role != "passenger":
        raise HTTPException(status_code=403, detail="Only passengers can update quick places")

    label = DEFAULT_PLACE_LABELS.get(key)
    if label is None:
        raise HTTPException(status_code=400, detail="Unsupported quick place key")

    place = db.execute(
        select(PassengerQuickPlace).where(
            PassengerQuickPlace.user_id == current_user.id,
            PassengerQuickPlace.key == key,
        )
    ).scalar_one_or_none()

    if place is None:
        place = PassengerQuickPlace(
            user_id=current_user.id,
            key=key,
            label=label,
            **payload.model_dump(),
        )
        db.add(place)
    else:
        place.label = label
        place.address_line = payload.address_line
        place.lat = payload.lat
        place.lng = payload.lng
        place.note = payload.note

    db.commit()
    db.refresh(place)

    return PassengerPlaceItem(
        key=place.key,
        label=place.label,
        address_id=str(place.id),
        address_line=place.address_line,
        has_address=True,
    )


@router.get("/trips/search-config", response_model=TripSearchConfigResponse)
def get_trip_search_config(
    current_user: User = Depends(get_current_user),
) -> TripSearchConfigResponse:
    if current_user.role != "passenger":
        raise HTTPException(status_code=403, detail="Only passengers can access trip search config")

    return TripSearchConfigResponse(
        default_schedule="now",
        schedule_options=[
            ScheduleOption(id="now", label="Now"),
            ScheduleOption(id="later", label="Schedule"),
        ],
    )
