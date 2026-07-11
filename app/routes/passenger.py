from fastapi import APIRouter, Depends, HTTPException, Path
from datetime import timedelta
from math import asin, cos, radians, sin, sqrt
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db import get_db
from ..models import PassengerQuickPlace, Trip, User, phnom_penh_now
from ..schemas import (
    NearbyDriverItem,
    NearbyDriversResponse,
    PassengerPlaceItem,
    PassengerPlacesResponse,
    PassengerPlaceUpsert,
    RideChoiceOption,
    ScheduleBucketRange,
    ScheduleOption,
    TripSearchConfigResponse,
    TripRead,
)

router = APIRouter(prefix="/passenger", tags=["passenger"])


def _trip_coordinates(trip: Trip) -> tuple[float | None, float | None]:
    if trip.departure_lat is not None and trip.departure_lng is not None:
        return float(trip.departure_lat), float(trip.departure_lng)
    pickup_stop = trip.pickup_stop or {}
    lat = pickup_stop.get("latitude")
    lng = pickup_stop.get("longitude")
    try:
        if lat is None or lng is None:
            return None, None
        return float(lat), float(lng)
    except (TypeError, ValueError):
        return None, None

DEFAULT_PLACE_LABELS = {
    "home": "Home",
    "work": "Work",
}


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    earth_radius_km = 6371.0
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return 2 * earth_radius_km * asin(sqrt(a))


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
        default_schedule="any",
        schedule_options=[
            ScheduleOption(id="any", label="Any time"),
            ScheduleOption(id="now", label="Now"),
            ScheduleOption(id="morning", label="Morning"),
            ScheduleOption(id="afternoon", label="Afternoon"),
            ScheduleOption(id="evening", label="Evening"),
        ],
        ride_choices=[
            RideChoiceOption(
                id="economy",
                title="Economy",
                meta="2 mins",
                icon="directions_car_filled_rounded",
                color="#4169E1",
                seat_type=4,
            ),
            RideChoiceOption(
                id="comfort",
                title="Comfort",
                meta="4 mins",
                icon="airport_shuttle_rounded",
                color="#697588",
                seat_type=15,
            ),
            RideChoiceOption(
                id="van_16",
                title="16 Seats",
                meta="5 mins",
                icon="airport_shuttle_rounded",
                color="#2F7D6B",
                seat_type=16,
            ),
            RideChoiceOption(
                id="sleeping_bus",
                title="Sleeping Bus",
                meta="7 mins",
                icon="airline_seat_individual_suite_rounded",
                color="#8B5E34",
                seat_type=23,
            ),
            RideChoiceOption(
                id="premium",
                title="Premium",
                meta="6 mins",
                icon="local_taxi_rounded",
                color="#353B4C",
                seat_type=30,
            ),
            RideChoiceOption(
                id="xl",
                title="XL",
                meta="8 mins",
                icon="directions_bus_filled_rounded",
                color="#4D5568",
                seat_type=45,
            ),
            RideChoiceOption(
                id="more",
                title="More",
                meta="",
                icon="grid_view_rounded",
                color="#697588",
                is_more=True,
            ),
        ],
        timezone="Asia/Phnom_Penh",
        schedule_bucket_ranges=[
            ScheduleBucketRange(id="morning", start="05:00", end="11:59"),
            ScheduleBucketRange(id="afternoon", start="12:00", end="16:59"),
            ScheduleBucketRange(id="evening", start="17:00", end="21:59"),
        ],
    )


@router.get("/nearby-drivers", response_model=NearbyDriversResponse)
def get_nearby_drivers(
    lat: float,
    lng: float,
    radius_km: float,
    seat_type: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NearbyDriversResponse:
    if current_user.role != "passenger":
        raise HTTPException(status_code=403, detail="Only passengers can access nearby drivers")

    if radius_km <= 0:
        raise HTTPException(status_code=400, detail="radius_km must be greater than 0")
    if seat_type is not None and seat_type not in (4, 15, 16, 23, 30, 45):
        raise HTTPException(status_code=400, detail="seat_type must be one of: 4, 15, 16, 23, 30, 45")

    now = phnom_penh_now()
    # Keep live data reasonably fresh while avoiding empty results for normal demo usage.
    fresh_threshold = now - timedelta(minutes=30)
    rows = db.execute(
        select(Trip).where(
            Trip.status.in_(("scheduled", "active")),
            Trip.live_location_expires_at.is_not(None),
            Trip.live_location_expires_at > now,
        )
    ).scalars().all()

    drivers: list[NearbyDriverItem] = []
    for trip in rows:
        trip_seat_type = trip.total_seats
        if seat_type is not None:
            if trip_seat_type != seat_type:
                continue
            if trip.available_seats <= 0:
                continue
            if trip.live_location_updated_at is None or trip.live_location_updated_at < fresh_threshold:
                continue

        trip_lat, trip_lng = _trip_coordinates(trip)
        if trip_lat is None or trip_lng is None:
            continue
        if _haversine_km(lat, lng, trip_lat, trip_lng) <= radius_km:
            drivers.append(
                NearbyDriverItem(
                    trip_id=trip.id,
                    driver_id=trip.driver_id,
                    lat=trip_lat,
                    lng=trip_lng,
                    heading=trip.live_heading,
                    speed_kph=float(trip.live_speed_kph) if trip.live_speed_kph is not None else None,
                    seat_type=trip_seat_type,
                    total_seats=trip.total_seats,
                    available_seats=trip.available_seats,
                    updated_at=trip.live_location_updated_at,
                    expires_at=trip.live_location_expires_at,
                    auto_repeat_weekly=trip.auto_repeat_weekly,
                )
            )

    return NearbyDriversResponse(drivers=drivers)


@router.get("/recommended-trips", response_model=list[TripRead])
def get_recommended_trips(
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TripRead]:
    if current_user.role != "passenger":
        raise HTTPException(status_code=403, detail="Only passengers can view recommended trips")

    from sqlalchemy.orm import selectinload
    from ..models import Trip
    from .travel import _build_trip_read, _expire_stale_trips_and_bookings

    _expire_stale_trips_and_bookings(db)
    now = phnom_penh_now()

    query = (
        select(Trip)
        .options(selectinload(Trip.driver), selectinload(Trip.vehicle), selectinload(Trip.bookings))
        .where(
            Trip.status == "scheduled",
            Trip.departure_time > now,
            Trip.available_seats > 0,
        )
        .order_by(Trip.departure_time.asc())
        .limit(limit)
    )
    rows = db.execute(query).scalars().all()
    return [_build_trip_read(row) for row in rows]


@router.get("/trips", response_model=list[TripRead])
def list_passenger_trips(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TripRead]:
    if current_user.role != "passenger":
        raise HTTPException(status_code=403, detail="Only passengers can view trips")

    from sqlalchemy.orm import selectinload
    from ..models import Trip
    from .travel import _build_trip_read, _expire_stale_trips_and_bookings

    safe_limit = max(1, min(limit, 500))
    _expire_stale_trips_and_bookings(db)
    now = phnom_penh_now()

    query = (
        select(Trip)
        .options(selectinload(Trip.driver), selectinload(Trip.vehicle), selectinload(Trip.bookings))
        .where(
            Trip.status == "scheduled",
            Trip.departure_time > now,
            Trip.available_seats > 0,
        )
        .order_by(Trip.departure_time.asc())
        .limit(safe_limit)
    )
    rows = db.execute(query).scalars().all()
    return [_build_trip_read(row) for row in rows]
