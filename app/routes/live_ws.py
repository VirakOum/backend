from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..db import SessionLocal
from ..models import AuthToken, Booking, BookingLiveLocation, Trip, User, phnom_penh_now

router = APIRouter(prefix="/travel/live", tags=["travel-live"])


class LiveLocationHub:
    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, websocket: WebSocket, rooms: set[str]) -> None:
        await websocket.accept()
        websocket.state.live_rooms = rooms
        for room in rooms:
            self._rooms[room].add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        rooms = getattr(websocket.state, "live_rooms", set())
        for room in rooms:
            sockets = self._rooms.get(room)
            if sockets is None:
                continue
            sockets.discard(websocket)
            if not sockets:
                self._rooms.pop(room, None)

    async def broadcast(self, room: str, payload: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for websocket in tuple(self._rooms.get(room, ())):
            try:
                await websocket.send_json(payload)
            except RuntimeError:
                dead.append(websocket)
        for websocket in dead:
            self.disconnect(websocket)


hub = LiveLocationHub()


def _room_for_trip(trip_id: UUID | str) -> str:
    return f"trip:{trip_id}"


def _room_for_booking(booking_id: UUID | str) -> str:
    return f"booking:{booking_id}"


def _authorized_rooms(
    user: User,
    trip_id: str | None,
    booking_id: str | None,
) -> set[str]:
    """Resolve realtime rooms without exposing another passenger's location."""
    rooms: set[str] = set()
    with SessionLocal() as db:
        booking: Booking | None = None
        if booking_id:
            try:
                booking = db.execute(
                    select(Booking)
                    .options(selectinload(Booking.trip))
                    .where(Booking.id == UUID(booking_id))
                ).scalar_one_or_none()
            except (TypeError, ValueError):
                booking = None

        if user.role == "passenger":
            if booking is not None and booking.passenger_id == user.id:
                # Passenger sockets are booking-scoped. Driver updates are also
                # fanned out to this room, so passengers never need the wider
                # trip room that contains other passengers' locations.
                rooms.add(_room_for_booking(booking.id))
            return rooms

        if user.role != "driver":
            return rooms

        if trip_id:
            try:
                trip = db.get(Trip, UUID(trip_id))
            except (TypeError, ValueError):
                trip = None
            if trip is not None and trip.driver_id == user.id:
                rooms.add(_room_for_trip(trip.id))

        if (
            booking is not None
            and booking.trip is not None
            and booking.trip.driver_id == user.id
        ):
            rooms.add(_room_for_booking(booking.id))
    return rooms


def _user_from_token(token: str | None) -> User | None:
    if not token:
        return None
    with SessionLocal() as db:
        auth_token = db.execute(
            select(AuthToken).where(AuthToken.token == token)
        ).scalar_one_or_none()
        if auth_token is None:
            return None
        return db.get(User, auth_token.user_id)


def _float_or_none(value: Any) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    try:
        return None if value is None else int(value)
    except (TypeError, ValueError):
        return None


async def _handle_driver_location(user: User, payload: dict[str, Any]) -> None:
    trip_id = payload.get("trip_id")
    lat = _float_or_none(payload.get("lat"))
    lng = _float_or_none(payload.get("lng"))
    if trip_id is None or lat is None or lng is None:
        return

    booking_ids: list[str] = []
    with SessionLocal() as db:
        trip = db.get(Trip, UUID(str(trip_id)))
        if (
            trip is None
            or trip.driver_id != user.id
            or trip.status not in {"scheduled", "active"}
        ):
            return

        now = phnom_penh_now()
        trip.live_lat = lat
        trip.live_lng = lng
        trip.live_heading = _int_or_none(payload.get("heading"))
        trip.live_speed_kph = _float_or_none(payload.get("speed_kph"))
        trip.live_location_updated_at = now
        trip.live_location_expires_at = now + timedelta(seconds=30)
        booking_ids = [
            str(value)
            for value in db.execute(
                select(Booking.id).where(
                    Booking.trip_id == trip.id,
                    Booking.status.in_(["pending", "confirmed"]),
                    Booking.pickup_status.in_(["pending", "driver_arrived"]),
                )
            ).scalars()
        ]
        db.commit()

    event = {
        "type": "driver_location",
        "trip_id": str(trip_id),
        "lat": lat,
        "lng": lng,
        "heading": _int_or_none(payload.get("heading")),
        "speed_kph": _float_or_none(payload.get("speed_kph")),
        "updated_at": phnom_penh_now().isoformat(),
    }
    await hub.broadcast(_room_for_trip(trip_id), event)
    for active_booking_id in booking_ids:
        await hub.broadcast(_room_for_booking(active_booking_id), event)


async def _handle_passenger_location(user: User, payload: dict[str, Any]) -> None:
    booking_id = payload.get("booking_id")
    lat = _float_or_none(payload.get("lat"))
    lng = _float_or_none(payload.get("lng"))
    if booking_id is None or lat is None or lng is None:
        return

    with SessionLocal() as db:
        booking = db.execute(
            select(Booking)
            .options(selectinload(Booking.trip))
            .where(Booking.id == UUID(str(booking_id)))
        ).scalar_one_or_none()
        if (
            booking is None
            or booking.passenger_id != user.id
            or booking.pickup_status not in {"pending", "driver_arrived"}
        ):
            return

        now = phnom_penh_now()
        loc = db.execute(
            select(BookingLiveLocation).where(
                BookingLiveLocation.booking_id == booking.id
            )
        ).scalar_one_or_none()
        if loc is None:
            loc = BookingLiveLocation(
                booking_id=booking.id,
                lat=lat,
                lng=lng,
                accuracy_m=_float_or_none(payload.get("accuracy_m")),
                updated_at=now,
                expires_at=now + timedelta(seconds=30),
            )
            db.add(loc)
        else:
            loc.lat = lat
            loc.lng = lng
            loc.accuracy_m = _float_or_none(payload.get("accuracy_m"))
            loc.updated_at = now
            loc.expires_at = now + timedelta(seconds=30)
        trip_id = booking.trip_id
        db.commit()

    event = {
        "type": "passenger_location",
        "booking_id": str(booking_id),
        "trip_id": str(trip_id),
        "lat": lat,
        "lng": lng,
        "accuracy_m": _float_or_none(payload.get("accuracy_m")),
        "updated_at": phnom_penh_now().isoformat(),
    }
    await hub.broadcast(_room_for_booking(booking_id), event)
    await hub.broadcast(_room_for_trip(trip_id), event)


@router.websocket("/ws")
async def travel_live_ws(websocket: WebSocket) -> None:
    user = _user_from_token(websocket.query_params.get("token"))
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    trip_id = websocket.query_params.get("trip_id")
    booking_id = websocket.query_params.get("booking_id")
    rooms = _authorized_rooms(user, trip_id, booking_id)
    if not rooms:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await hub.connect(websocket, rooms)
    try:
        while True:
            payload = await websocket.receive_json()
            event_type = payload.get("type")
            if event_type == "driver_location" and user.role == "driver":
                await _handle_driver_location(user, payload)
            elif event_type == "passenger_location" and user.role == "passenger":
                await _handle_passenger_location(user, payload)
    except WebSocketDisconnect:
        hub.disconnect(websocket)
    except Exception:
        hub.disconnect(websocket)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
