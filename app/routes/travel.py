import os
import re
from base64 import b64decode
from binascii import Error as Base64DecodeError
from copy import deepcopy

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload
from uuid import UUID
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from ..auth import get_current_user, hash_password, issue_token, verify_password
from ..config import ENABLE_DIGITAL_PAYMENT
from ..db import get_db
from ..models import Booking, BookingPaymentInstruction, DriverWalletEntry, NotificationPreference, Payment, SupportTicket, Trip, User, Vehicle, phnom_penh_now
from .driver_fee import (
    evaluate_driver_wallet_lock,
    get_or_create_driver_wallet,
    get_runtime_settings,
    snapshot_booking_fees,
)
from ..schemas import (
	ActiveBookingResponse,
	AuthResponse,
	BookingCreate,
	BookingRead,
	BookingWithTripRead,
	DriverArrivedRequest,
	LoginRequest,
	NotificationPreferences,
	NotificationPreferencesRead,
	PaymentInstructionUploadRequest,
	PaymentInstructionRead,
	PaymentCreate,
	PaymentRead,
	PaymentStatusUpdate,
	SafetyConfigResponse,
	SupportConfigResponse,
	SupportTicketCreate,
	SupportTicketRead,
	TripCreate,
	TripDriverInfo,
	TripLiveLocationResponse,
	TripLiveLocationInfo,
	TripLiveLocationUpdate,
	TripPromotionInfo,
	TripRead,
	TripUpdate,
	TripVehicleInfo,
	UserCreate,
	UserRead,
	VehicleCreate,
	VehicleRead,
	VehicleUpdate,
	WalletSummaryResponse,
	WalletTransactionItem,
)

router = APIRouter(prefix="/travel", tags=["travel"])

BOOKING_SEAT_HOLD_STATUSES = {"pending", "confirmed"}
DEFAULT_CURRENCY = "USD"
ABA_PAYMENT_LINK_RE = re.compile(r"https://pay\.ababank\.com/[a-zA-Z0-9/]+")

LEGACY_PAYMENT_METHOD_MAP = {
	"cash_on_arrival": "cash",
	"khqr": "aba",
}
LEGACY_PAYMENT_STATUS_MAP = {
	"opened": "pending",
	"failed": "pending",
	"cancelled": "pending",
}


def _cleanup_expired_live_locations(db: Session) -> None:
	now = phnom_penh_now()
	expired = db.execute(
		select(Trip).where(
			Trip.live_location_expires_at.is_not(None),
			Trip.live_location_expires_at <= now,
		)
	).scalars().all()
	if not expired:
		return
	for trip in expired:
		trip.departure_lat = None
		trip.departure_lng = None
		trip.live_heading = None
		trip.live_speed_kph = None
		trip.live_location_updated_at = None
		trip.live_location_expires_at = None
	db.commit()


def _parse_iso_datetime_or_date(value: str) -> tuple[datetime, bool]:
	text = value.strip()
	if not text:
		raise ValueError("empty")
	try:
		d = date.fromisoformat(text)
		return datetime.combine(d, time(0, 0, 0)), False
	except ValueError:
		pass
	# Accept ISO 8601 datetime strings like 2026-05-26T17:08:15.760793 or with Z suffix
	dt_text = text.replace("Z", "+00:00")
	dt = datetime.fromisoformat(dt_text)
	return dt, True


def _money(value: Decimal) -> Decimal:
	return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _final_price_per_seat(trip: Trip) -> Decimal:
	price = Decimal(str(trip.price_per_seat))
	discount_percent = trip.promotion_discount_percent or 0
	if not trip.promotion_label or discount_percent <= 0:
		return _money(price)
	discount_multiplier = (Decimal("100") - Decimal(discount_percent)) / Decimal("100")
	return _money(price * discount_multiplier)


def _build_promotion(trip: Trip) -> TripPromotionInfo | None:
	discount_percent = trip.promotion_discount_percent or 0
	if not trip.promotion_label or discount_percent <= 0:
		return None
	return TripPromotionInfo(
		label=trip.promotion_label,
		discount_percent=discount_percent,
		original_price_per_seat=float(_money(Decimal(str(trip.price_per_seat)))),
		final_price_per_seat=float(_final_price_per_seat(trip)),
		currency=DEFAULT_CURRENCY,
	)


def _build_live_location(trip: Trip) -> TripLiveLocationInfo | None:
	if trip.departure_lat is None or trip.departure_lng is None or trip.live_location_expires_at is None:
		return None
	return TripLiveLocationInfo(
		lat=float(trip.departure_lat),
		lng=float(trip.departure_lng),
		heading=trip.live_heading,
		speed_kph=float(trip.live_speed_kph) if trip.live_speed_kph is not None else None,
		updated_at=trip.live_location_updated_at,
		expires_at=trip.live_location_expires_at,
	)


def _booked_seat_numbers(trip: Trip) -> list[int]:
	booked: set[int] = set()
	for booking in trip.bookings:
		if booking.status in BOOKING_SEAT_HOLD_STATUSES:
			booked.update(booking.seat_numbers)
	return sorted(booked)


def _app_bookings_for_trip(trip: Trip) -> list[Booking]:
	return [
		booking
		for booking in trip.bookings
		if booking.status in BOOKING_SEAT_HOLD_STATUSES
	]


def _available_seat_numbers(trip: Trip) -> list[int]:
	booked = set(_booked_seat_numbers(trip))
	open_seats = [seat_number for seat_number in range(1, trip.total_seats + 1) if seat_number not in booked]
	return open_seats[: max(0, trip.available_seats)]


def _build_trip_read(trip: Trip) -> TripRead:
	live_location = _build_live_location(trip)
	booked_seat_numbers = _booked_seat_numbers(trip)
	available_seat_numbers = _available_seat_numbers(trip)
	app_bookings = _app_bookings_for_trip(trip)
	app_booked_seat_count = sum(len(booking.seat_numbers) for booking in app_bookings)
	driver = None
	if trip.driver is not None:
		driver = TripDriverInfo(
			id=trip.driver.id,
			full_name=trip.driver.full_name,
			avatar_url=trip.driver.avatar_url,
			is_verified=trip.driver.is_verified,
			rating_avg=float(trip.driver.rating_avg or 0),
			rating_count=trip.driver.rating_count or 0,
			completed_trips=trip.driver.completed_trips or 0,
		)

	vehicle = None
	if trip.vehicle is not None:
		vehicle = TripVehicleInfo(
			id=trip.vehicle.id,
			type=trip.vehicle.vehicle_type,
			model=trip.vehicle.model,
			plate_number=trip.vehicle.plate_number,
			color=trip.vehicle.color,
			seat_type=trip.vehicle.seat_type,
		)

	return TripRead.model_validate(trip).model_copy(
		update={
			"live_lat": live_location.lat if live_location else None,
			"live_lng": live_location.lng if live_location else None,
			"driver": driver,
			"vehicle": vehicle,
			"promotion": _build_promotion(trip),
			"live_location": live_location,
			"booked_seat_numbers": booked_seat_numbers,
			"available_seat_numbers": available_seat_numbers,
			"appBookedSeatCount": app_booked_seat_count,
			"appBookingCount": len(app_bookings),
		}
	)


def _booking_payment_status(booking: Booking) -> str:
	if any(payment.status == "success" for payment in booking.payments):
		return "paid"
	if any(payment.status == "failed" for payment in booking.payments):
		return "failed"
	return booking.payment_status


def _normalized_payment_method(value: str | None) -> str:
	if value is None:
		return "cash"
	return LEGACY_PAYMENT_METHOD_MAP.get(value, value)


def _normalized_payment_status(value: str | None) -> str:
	if value is None:
		return "pending"
	return LEGACY_PAYMENT_STATUS_MAP.get(value, value)


def _digital_payment_enabled(db: Session) -> bool:
	return get_runtime_settings(db).enable_digital_payment


def _assert_digital_payment_enabled(db: Session) -> None:
	if not _digital_payment_enabled(db):
		raise HTTPException(
			status_code=403,
			detail="Digital payment is coming soon. Cash payment is the only live method right now.",
		)


def _sync_booking_completion_from_trip(
	db: Session,
	*,
	trip: Trip,
) -> None:
	boarded_bookings = [
		booking
		for booking in trip.bookings
		if booking.status == "confirmed"
		and booking.pickup_status == "passenger_boarded"
	]
	no_show_bookings = [
		booking
		for booking in trip.bookings
		if booking.status == "confirmed"
		and booking.pickup_status != "passenger_boarded"
	]

	if not boarded_bookings and no_show_bookings:
		for booking in no_show_bookings:
			trip.available_seats += len(booking.seat_numbers or [])
			booking.status = "cancelled"
			booking.payment_status = "pending"

	for booking in boarded_bookings:
		snapshot_booking_fees(db, booking)
		if booking.wallet_entries:
			booking.pickup_status = "completed"
			booking.payment_status = "postpaid"
			continue

		trip_price = Decimal(str(booking.total_price or 0))
		cash_collected_khr = int(_money(trip_price) * Decimal("4000"))
		driver_wallet = get_or_create_driver_wallet(db, driver_id=trip.driver_id)
		wallet_entry = DriverWalletEntry(
			driver_id=trip.driver_id,
			trip_id=trip.id,
			booking_id=booking.id,
			entry_type="trip_service_fee",
			payment_method=_normalized_payment_method(booking.payment_method),
			membership_code_snapshot=booking.membership_code_snapshot or "normal",
			membership_label_snapshot=booking.membership_label_snapshot or "Normal User",
			passenger_count=len(booking.seat_numbers or []),
			cash_collected_khr=cash_collected_khr,
			service_fee_usd=float(booking.service_fee_total_usd or 0),
			service_fee_khr=int(booking.service_fee_total_khr or 0),
			status="owed",
			notes="Auto-posted when driver completed the trip.",
		)
		db.add(wallet_entry)

		driver_wallet.service_fee_owed_usd = float(
			Decimal(str(driver_wallet.service_fee_owed_usd or 0))
			+ Decimal(str(booking.service_fee_total_usd or 0)),
		)
		driver_wallet.service_fee_owed_khr = int(driver_wallet.service_fee_owed_khr or 0) + int(
			booking.service_fee_total_khr or 0
		)
		driver_wallet.total_owed_usd = float(
			Decimal(str(driver_wallet.total_owed_usd or 0))
			+ Decimal(str(booking.service_fee_total_usd or 0)),
		)
		driver_wallet.total_owed_khr = int(driver_wallet.total_owed_khr or 0) + int(
			booking.service_fee_total_khr or 0
		)
		driver_wallet.last_entry_posted_at = phnom_penh_now()

		booking.pickup_status = "completed"
		booking.payment_status = "postpaid"

	settings = get_runtime_settings(db)
	evaluate_driver_wallet_lock(
		db,
		wallet=get_or_create_driver_wallet(db, driver_id=trip.driver_id),
		settings=settings,
	)


def _build_payment_instruction_read(
	booking: Booking,
	instruction: BookingPaymentInstruction | None,
) -> PaymentInstructionRead | None:
	if instruction is None:
		return None
	return PaymentInstructionRead(
		booking_id=booking.id,
		trip_id=booking.trip_id,
		source_type=instruction.source_type,
		deep_link_url=instruction.deep_link_url,
		qr_image_url=instruction.qr_image_url,
		qr_payload=instruction.qr_payload,
		raw_message=instruction.raw_message,
		parse_status=instruction.parse_status,
		bank_provider=instruction.bank_provider,
		payment_status=_normalized_payment_status(_booking_payment_status(booking)),
		captured_at=instruction.captured_at,
		expires_at=instruction.expires_at,
	)


def _build_booking_with_trip_read(booking: Booking) -> BookingWithTripRead:
	return BookingWithTripRead(
		id=booking.id,
		trip_id=booking.trip_id,
		passenger_id=booking.passenger_id,
		seat_numbers=booking.seat_numbers,
		total_price=float(booking.total_price),
		currency=DEFAULT_CURRENCY,
		payment_method=_normalized_payment_method(booking.payment_method),
		payment_status=_normalized_payment_status(_booking_payment_status(booking)),
		pickup_status=booking.pickup_status,
		driver_arrived_at=booking.driver_arrived_at,
		status=booking.status,
		created_at=booking.created_at,
		payment_instruction=_build_payment_instruction_read(booking, booking.payment_instruction),
		trip=_build_trip_read(booking.trip) if booking.trip is not None else None,
	)


def _empty_payment_instruction(booking: Booking) -> PaymentInstructionRead:
	return PaymentInstructionRead(
		booking_id=booking.id,
		trip_id=booking.trip_id,
		source_type="none",
		parse_status="missing",
		payment_status=_normalized_payment_status(_booking_payment_status(booking)),
	)


def _get_or_create_payment_instruction(
	db: Session,
	booking: Booking,
) -> BookingPaymentInstruction:
	if booking.payment_instruction is not None:
		return booking.payment_instruction
	instruction = BookingPaymentInstruction(
		booking_id=booking.id,
		source_type="none",
		parse_status="missing",
		payment_status=_booking_payment_status(booking),
		captured_at=phnom_penh_now(),
	)
	db.add(instruction)
	db.flush()
	booking.payment_instruction = instruction
	return instruction


def _instruction_parse_status(
	*,
	deep_link_url: str | None,
	qr_payload: str | None,
	qr_image_url: str | None,
	raw_message: str | None,
) -> str:
	if deep_link_url is not None or qr_payload is not None:
		return "parsed"
	if qr_image_url is not None or raw_message is not None:
		return "failed"
	return "missing"


def _apply_payment_instruction_capture(
	instruction: BookingPaymentInstruction,
	payload: DriverArrivedRequest | None,
) -> None:
	raw_message = payload.raw_message.strip() if payload is not None and payload.raw_message else None
	deep_link_url = payload.deep_link_url if payload is not None else None
	if raw_message and deep_link_url is None:
		match = ABA_PAYMENT_LINK_RE.search(raw_message)
		if match is not None:
			deep_link_url = match.group(0)

	instruction.raw_message = raw_message
	instruction.deep_link_url = deep_link_url
	instruction.qr_image_url = payload.qr_image_url if payload is not None else None
	instruction.qr_payload = payload.qr_payload if payload is not None else None
	instruction.expires_at = payload.expires_at if payload is not None else None
	instruction.captured_at = phnom_penh_now()

	if payload is not None and payload.bank_provider is not None:
		instruction.bank_provider = payload.bank_provider
	elif deep_link_url is not None:
		instruction.bank_provider = "ABA"
	elif payload is not None and (payload.qr_payload is not None or payload.qr_image_url is not None):
		instruction.bank_provider = "KHQR"
	else:
		instruction.bank_provider = None

	if payload is not None and payload.source_type is not None:
		instruction.source_type = payload.source_type
	elif raw_message is not None:
		instruction.source_type = "text"
	elif payload is not None and payload.qr_payload is not None:
		instruction.source_type = "qr_payload"
	elif payload is not None and payload.qr_image_url is not None:
		instruction.source_type = "qr_image"
	elif deep_link_url is not None:
		instruction.source_type = "manual"
	else:
		instruction.source_type = "none"

	instruction.parse_status = _instruction_parse_status(
		deep_link_url=instruction.deep_link_url,
		qr_payload=instruction.qr_payload,
		qr_image_url=instruction.qr_image_url,
		raw_message=instruction.raw_message,
	)


def _assert_driver_vehicle_access(vehicle: Vehicle | None, current_user: User) -> Vehicle:
	if vehicle is None:
		raise HTTPException(status_code=404, detail="Vehicle not found")
	if current_user.role != "driver" or vehicle.owner_id != current_user.id:
		raise HTTPException(status_code=403, detail="You can only manage your own vehicles")
	return vehicle


def _assert_driver_trip_access(trip: Trip | None, current_user: User) -> Trip:
	if trip is None:
		raise HTTPException(status_code=404, detail="Trip not found")
	if current_user.role != "driver" or trip.driver_id != current_user.id:
		raise HTTPException(status_code=403, detail="You can only manage your own trips")
	return trip


def _load_trip_for_read(db: Session, trip_id: UUID) -> Trip | None:
	return db.execute(
		select(Trip)
		.options(selectinload(Trip.driver), selectinload(Trip.vehicle), selectinload(Trip.bookings))
		.where(Trip.id == trip_id)
	).scalar_one_or_none()


def _clone_json_value(value: dict | None) -> dict | None:
    return deepcopy(value) if value is not None else None


def _validate_trip_route_stop_pair(
    *,
    route_data: dict | None,
    stop_data: dict | None,
    route_field_name: str,
    stop_field_name: str,
) -> None:
    if route_data is None or stop_data is None:
        return

    route_commune_code = route_data.get("commune_code")
    stop_commune_code = stop_data.get("commune_code")
    if route_commune_code and stop_commune_code and route_commune_code != stop_commune_code:
        raise HTTPException(
            status_code=400,
            detail=f"{stop_field_name}.commune_code must match {route_field_name}.commune_code",
        )


def _validate_trip_route_stop_payload(data: dict) -> None:
    _validate_trip_route_stop_pair(
        route_data=data.get("departure_route"),
        stop_data=data.get("pickup_stop"),
        route_field_name="departure_route",
        stop_field_name="pickup_stop",
    )
    _validate_trip_route_stop_pair(
        route_data=data.get("destination_route"),
        stop_data=data.get("dropoff_stop"),
        route_field_name="destination_route",
        stop_field_name="dropoff_stop",
    )


def _normalize_trip_schedule_data(data: dict) -> dict:
	repeat_mode = data.get("repeat_mode")
	if repeat_mode is None:
		repeat_mode = "weekly" if data.get("auto_repeat_weekly") else "none"
	data["repeat_mode"] = repeat_mode
	data["auto_repeat_weekly"] = repeat_mode == "weekly"

	departure_time_value = data.get("departure_time")
	if repeat_mode == "weekly" and data.get("recurring_day_of_week") is None and departure_time_value is not None:
		data["recurring_day_of_week"] = departure_time_value.weekday()
	if repeat_mode in {"daily", "weekly"} and data.get("recurring_departure_time") is None and departure_time_value is not None:
		data["recurring_departure_time"] = departure_time_value.time().replace(second=0, microsecond=0)
	if repeat_mode == "none":
		data["recurring_day_of_week"] = None
		data["recurring_departure_time"] = None

	if not data.get("has_return_schedule"):
		data["has_return_schedule"] = False
		data["return_departure_time"] = None
	return data


def _sync_return_trip(db: Session, trip: Trip) -> None:
    if not trip.has_return_schedule or trip.return_departure_time is None:
        if trip.return_trip_id is not None:
            return_trip = db.get(Trip, trip.return_trip_id)
            if return_trip is not None:
                return_trip.status = "cancelled"
                return_trip.return_trip_id = None
        trip.return_trip_id = None
        trip.return_departure_time = None
        return

    return_trip = db.get(Trip, trip.return_trip_id) if trip.return_trip_id is not None else None
    return_data = {
        "driver_id": trip.driver_id,
        "vehicle_id": trip.vehicle_id,
        "departure_province": trip.destination_province,
        "destination_province": trip.departure_province,
        "departure_time": trip.return_departure_time,
        "departure_lat": None,
        "departure_lng": None,
        "departure_route": _clone_json_value(trip.destination_route),
        "destination_route": _clone_json_value(trip.departure_route),
        "pickup_stop": _clone_json_value(trip.dropoff_stop),
        "dropoff_stop": _clone_json_value(trip.pickup_stop),
        "live_heading": None,
        "live_speed_kph": None,
        "live_location_updated_at": None,
        "live_location_expires_at": None,
        "repeat_mode": trip.repeat_mode,
        "auto_repeat_weekly": trip.repeat_mode == "weekly",
        "recurring_day_of_week": trip.return_departure_time.weekday() if trip.repeat_mode == "weekly" else None,
        "recurring_departure_time": trip.return_departure_time.time().replace(second=0, microsecond=0) if trip.repeat_mode in {"daily", "weekly"} else None,
        "has_return_schedule": False,
        "return_departure_time": None,
        "promotion_label": trip.promotion_label,
        "promotion_discount_percent": trip.promotion_discount_percent,
        "price_per_seat": trip.price_per_seat,
        "total_seats": trip.total_seats,
        "available_seats": trip.total_seats,
        "status": trip.status,
    }
    if return_trip is None:
        return_trip = Trip(**return_data)
        db.add(return_trip)
        db.flush()
        trip.return_trip_id = return_trip.id
    else:
        for field, value in return_data.items():
            setattr(return_trip, field, value)
    return_trip.return_trip_id = trip.id


def _apply_trip_update(db: Session, trip: Trip, payload: TripUpdate, current_user: User) -> None:
    update_data = payload.model_dump(exclude_unset=True)
    for required_field in [
        "departure_province",
        "destination_province",
        "departure_time",
        "price_per_seat",
        "total_seats",
        "available_seats",
        "status",
    ]:
        if required_field in update_data and update_data[required_field] is None:
            raise HTTPException(status_code=422, detail=f"{required_field} cannot be null")
    if "vehicle_id" in update_data and update_data["vehicle_id"] is not None:
        vehicle = db.get(Vehicle, update_data["vehicle_id"])
        _assert_driver_vehicle_access(vehicle, current_user)
    normalized = _normalize_trip_schedule_data(
        {
            "repeat_mode": trip.repeat_mode,
            "auto_repeat_weekly": trip.auto_repeat_weekly,
            "recurring_day_of_week": trip.recurring_day_of_week,
            "recurring_departure_time": trip.recurring_departure_time,
            "has_return_schedule": trip.has_return_schedule,
            "return_departure_time": trip.return_departure_time,
            "departure_time": trip.departure_time,
            "departure_route": _clone_json_value(trip.departure_route),
            "destination_route": _clone_json_value(trip.destination_route),
            "pickup_stop": _clone_json_value(trip.pickup_stop),
            "dropoff_stop": _clone_json_value(trip.dropoff_stop),
            **update_data,
        }
    )
    _validate_trip_route_stop_payload(normalized)
    for field in [
        "repeat_mode",
        "auto_repeat_weekly",
        "recurring_day_of_week",
        "recurring_departure_time",
        "has_return_schedule",
        "return_departure_time",
    ]:
        if field in normalized:
            update_data[field] = normalized[field]
    if update_data.get("has_return_schedule") and update_data.get("return_departure_time") is None:
        raise HTTPException(status_code=422, detail="return_departure_time is required when has_return_schedule is true")
    for field, value in update_data.items():
        setattr(trip, field, value)
    if trip.available_seats > trip.total_seats:
        raise HTTPException(status_code=400, detail="available_seats cannot exceed total_seats")


def _get_or_create_notification_preferences(db: Session, user: User) -> NotificationPreference:
	preferences = db.execute(
		select(NotificationPreference).where(NotificationPreference.user_id == user.id)
	).scalar_one_or_none()
	if preferences is not None:
		return preferences
	preferences = NotificationPreference(user_id=user.id)
	db.add(preferences)
	db.commit()
	db.refresh(preferences)
	return preferences


@router.post("/auth/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: UserCreate, db: Session = Depends(get_db)) -> AuthResponse:
	existing = db.execute(select(User).where(User.phone == payload.phone)).scalar_one_or_none()
	if existing is not None:
		raise HTTPException(status_code=409, detail="Phone already exists")

	user_data = payload.model_dump(exclude={"password"})
	user = User(**user_data, password_hash=hash_password(payload.password))
	db.add(user)
	db.commit()
	db.refresh(user)
	token = issue_token(db, user)
	return AuthResponse(token=token, user=UserRead.model_validate(user))


@router.post("/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
	user = db.execute(select(User).where(User.phone == payload.phone)).scalar_one_or_none()
	if user is None or not verify_password(payload.password, user.password_hash):
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid phone or password")

	token = issue_token(db, user)
	return AuthResponse(token=token, user=UserRead.model_validate(user))


@router.get("/auth/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)) -> UserRead:
	return UserRead.model_validate(current_user)


@router.get("/users/{user_id}", response_model=UserRead)
def get_user(
	user_id: UUID,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> UserRead:
	user = db.get(User, user_id)
	if user is None:
		raise HTTPException(status_code=404, detail="User not found")
	if current_user.id != user.id:
		raise HTTPException(status_code=403, detail="You can only view your own profile")
	return UserRead.model_validate(user)


@router.post("/vehicles", response_model=VehicleRead, status_code=status.HTTP_201_CREATED)
def create_vehicle(
	payload: VehicleCreate,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> VehicleRead:
	if current_user.role != "driver":
		raise HTTPException(status_code=403, detail="Only drivers can register vehicles")

	existing_plate = db.execute(
		select(Vehicle).where(Vehicle.plate_number == payload.plate_number)
	).scalar_one_or_none()
	if existing_plate is not None:
		raise HTTPException(status_code=409, detail="Plate number already exists")

	vehicle = Vehicle(**payload.model_dump(), owner_id=current_user.id)
	db.add(vehicle)
	db.commit()
	db.refresh(vehicle)
	return VehicleRead.model_validate(vehicle)


@router.get("/vehicles/{vehicle_id}", response_model=VehicleRead)
def get_vehicle(
	vehicle_id: UUID,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> VehicleRead:
	vehicle = db.get(Vehicle, vehicle_id)
	if vehicle is None:
		raise HTTPException(status_code=404, detail="Vehicle not found")
	if vehicle.owner_id != current_user.id:
		raise HTTPException(status_code=403, detail="You can only view your own vehicles")
	return VehicleRead.model_validate(vehicle)


@router.get("/driver/vehicles", response_model=list[VehicleRead])
def list_driver_vehicles(
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> list[VehicleRead]:
	if current_user.role != "driver":
		raise HTTPException(status_code=403, detail="Only drivers can list their vehicles")
	rows = db.execute(
		select(Vehicle)
		.where(Vehicle.owner_id == current_user.id)
		.order_by(Vehicle.created_at.desc())
	).scalars().all()
	return [VehicleRead.model_validate(row) for row in rows]


@router.put("/vehicles/{vehicle_id}", response_model=VehicleRead)
@router.patch("/vehicles/{vehicle_id}", response_model=VehicleRead)
def update_vehicle(
	vehicle_id: UUID,
	payload: VehicleUpdate,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> VehicleRead:
	vehicle = _assert_driver_vehicle_access(db.get(Vehicle, vehicle_id), current_user)
	update_data = payload.model_dump(exclude_unset=True)
	if "plate_number" in update_data and update_data["plate_number"] is None:
		raise HTTPException(status_code=422, detail="plate_number cannot be null")
	if "seat_type" in update_data and update_data["seat_type"] is None:
		raise HTTPException(status_code=422, detail="seat_type cannot be null")
	if "seat_type" in update_data and update_data["seat_type"] not in {4, 15, 16, 23, 30, 45}:
		raise HTTPException(status_code=422, detail="Invalid seat_type")
	if "plate_number" in update_data and update_data["plate_number"] != vehicle.plate_number:
		existing_plate = db.execute(
			select(Vehicle).where(Vehicle.plate_number == update_data["plate_number"])
		).scalar_one_or_none()
		if existing_plate is not None:
			raise HTTPException(status_code=409, detail="Plate number already exists")
	for field, value in update_data.items():
		setattr(vehicle, field, value)
	db.commit()
	db.refresh(vehicle)
	return VehicleRead.model_validate(vehicle)


@router.delete("/vehicles/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(
	vehicle_id: UUID,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> None:
	vehicle = _assert_driver_vehicle_access(db.get(Vehicle, vehicle_id), current_user)
	for trip in db.execute(select(Trip).where(Trip.vehicle_id == vehicle.id)).scalars().all():
		trip.vehicle_id = None
	db.delete(vehicle)
	db.commit()
	return None


@router.post("/trips", response_model=TripRead, status_code=status.HTTP_201_CREATED)
def create_trip(
	payload: TripCreate,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> TripRead:
    if current_user.role != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can create trips")
    driver_wallet = get_or_create_driver_wallet(db, driver_id=current_user.id)
    evaluate_driver_wallet_lock(db, wallet=driver_wallet, settings=get_runtime_settings(db))
    if driver_wallet.is_locked:
        raise HTTPException(status_code=403, detail=driver_wallet.locked_reason)

    if payload.vehicle_id is not None:
        vehicle = db.get(Vehicle, payload.vehicle_id)
        if vehicle is None:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        if vehicle.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Vehicle does not belong to the current user")

    if payload.available_seats > payload.total_seats:
        raise HTTPException(status_code=400, detail="available_seats cannot exceed total_seats")

    trip_data = _normalize_trip_schedule_data(payload.model_dump())
    _validate_trip_route_stop_payload(trip_data)
    if trip_data["has_return_schedule"] and trip_data.get("return_departure_time") is None:
        raise HTTPException(status_code=422, detail="return_departure_time is required when has_return_schedule is true")
    if trip_data.get("departure_lat") is not None and trip_data.get("departure_lng") is not None:
        if trip_data.get("live_location_expires_at") is None:
            trip_data["live_location_expires_at"] = payload.departure_time + timedelta(hours=24)
        trip_data["live_location_updated_at"] = phnom_penh_now()
    trip = Trip(**trip_data, driver_id=current_user.id)
    db.add(trip)
    db.flush()
    _sync_return_trip(db, trip)
    db.commit()
    created_trip = db.execute(
        select(Trip)
        .options(selectinload(Trip.driver), selectinload(Trip.vehicle), selectinload(Trip.bookings))
        .where(Trip.id == trip.id)
    ).scalar_one()
    return _build_trip_read(created_trip)


@router.get("/driver/trips", response_model=list[TripRead])
def list_driver_trips(
	status_filter: str | None = Query(default=None, alias="status", pattern="^(scheduled|active|completed|cancelled)$"),
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> list[TripRead]:
	if current_user.role != "driver":
		raise HTTPException(status_code=403, detail="Only drivers can list their trips")
	query = (
		select(Trip)
		.options(selectinload(Trip.driver), selectinload(Trip.vehicle), selectinload(Trip.bookings))
		.where(Trip.driver_id == current_user.id)
	)
	if status_filter is not None:
		query = query.where(Trip.status == status_filter)
	rows = db.execute(query.order_by(Trip.departure_time.desc())).scalars().all()
	return [_build_trip_read(row) for row in rows]


@router.put("/trips/{trip_id}", response_model=TripRead)
@router.patch("/trips/{trip_id}", response_model=TripRead)
def update_trip(
	trip_id: UUID,
	payload: TripUpdate,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> TripRead:
	trip = _assert_driver_trip_access(db.get(Trip, trip_id), current_user)
	if payload.status in {"scheduled", "active"}:
		driver_wallet = get_or_create_driver_wallet(db, driver_id=current_user.id)
		evaluate_driver_wallet_lock(db, wallet=driver_wallet, settings=get_runtime_settings(db))
		if driver_wallet.is_locked:
			raise HTTPException(status_code=403, detail=driver_wallet.locked_reason)
	_apply_trip_update(db, trip, payload, current_user)
	_sync_return_trip(db, trip)
	db.commit()
	updated_trip = _load_trip_for_read(db, trip.id)
	if updated_trip is None:
		raise HTTPException(status_code=404, detail="Trip not found")
	return _build_trip_read(updated_trip)


@router.get("/trips/search", response_model=list[TripRead])
def search_trips(
	departure_province: str = Query(min_length=1, max_length=50),
	destination_province: str = Query(min_length=1, max_length=50),
	journey_date: str | None = None,
	return_date: str | None = None,
	schedule: str | None = None,
	timezone: str = "Asia/Phnom_Penh",
	db: Session = Depends(get_db),
) -> list[TripRead]:
	if departure_province == destination_province:
		raise HTTPException(status_code=400, detail="departure_province and destination_province cannot be the same")
	try:
		tz = ZoneInfo(timezone)
	except ZoneInfoNotFoundError:
		raise HTTPException(status_code=422, detail="Invalid timezone value")

	normalized_schedule = (schedule or "").strip().lower() or "any"
	allowed_schedule = {"any", "now", "morning", "afternoon", "evening"}
	if normalized_schedule not in allowed_schedule:
		raise HTTPException(status_code=422, detail="Invalid schedule value")

	journey_dt: datetime | None = None
	journey_has_time = False
	if journey_date is not None and journey_date.strip():
		try:
			journey_dt, journey_has_time = _parse_iso_datetime_or_date(journey_date)
			if journey_dt.tzinfo is not None:
				journey_dt = journey_dt.astimezone(tz).replace(tzinfo=None)
		except ValueError:
			raise HTTPException(status_code=422, detail="Invalid journey_date format")

	return_dt: datetime | None = None
	return_has_time = False
	if return_date is not None and return_date.strip():
		try:
			return_dt, return_has_time = _parse_iso_datetime_or_date(return_date)
			if return_dt.tzinfo is not None:
				return_dt = return_dt.astimezone(tz).replace(tzinfo=None)
		except ValueError:
			raise HTTPException(status_code=422, detail="Invalid return_date format")
		if journey_dt is not None and return_dt < journey_dt:
			raise HTTPException(status_code=400, detail="return_date cannot be earlier than journey_date")

	_cleanup_expired_live_locations(db)

	base_query = (
			select(Trip)
			.options(selectinload(Trip.driver), selectinload(Trip.vehicle), selectinload(Trip.bookings))
		.where(
			Trip.departure_province == departure_province,
			Trip.destination_province == destination_province,
			Trip.status == "scheduled",
		)
		.order_by(Trip.departure_time.asc())
	)

	# Backward compatibility for older app versions.
	if journey_dt is None and normalized_schedule == "any":
		rows = db.execute(base_query).scalars().all()
		return [_build_trip_read(row) for row in rows]

	if journey_dt is None:
		raise HTTPException(status_code=422, detail="journey_date is required when schedule is provided")

	# Time-aware filtering:
	# - date-only journey_date => whole day window
	# - datetime journey_date => strictly after that exact moment
	# - return_date provided => upper bound at that exact datetime (or end-of-day if date-only)
	if journey_has_time:
		window_start = journey_dt
		start_operator = Trip.departure_time > window_start
	else:
		window_start = datetime.combine(journey_dt.date(), time(0, 0, 0))
		start_operator = Trip.departure_time >= window_start

	if return_dt is not None:
		if return_has_time:
			window_end = return_dt
		else:
			window_end = datetime.combine(return_dt.date(), time(23, 59, 59, 999999))
	else:
		window_end = datetime.combine(journey_dt.date(), time(23, 59, 59, 999999))

	base_query = base_query.where(
		start_operator,
		Trip.departure_time <= window_end,
	)
	rows = db.execute(base_query).scalars().all()

	now_local = datetime.now(tz).replace(tzinfo=None)
	if normalized_schedule == "any":
		filtered = rows
	elif normalized_schedule == "now":
		filtered = [row for row in rows if row.departure_time >= now_local]
	elif normalized_schedule == "morning":
		filtered = [row for row in rows if time(5, 0) <= row.departure_time.time() <= time(11, 59)]
	elif normalized_schedule == "afternoon":
		filtered = [row for row in rows if time(12, 0) <= row.departure_time.time() <= time(16, 59)]
	else:  # evening
		filtered = [row for row in rows if time(17, 0) <= row.departure_time.time() <= time(21, 59)]

	return [_build_trip_read(row) for row in filtered]


@router.get("/trips/{trip_id}", response_model=TripRead)
def get_trip(trip_id: UUID, db: Session = Depends(get_db)) -> TripRead:
	_cleanup_expired_live_locations(db)
	trip = db.execute(
		select(Trip)
		.options(selectinload(Trip.driver), selectinload(Trip.vehicle), selectinload(Trip.bookings))
		.where(Trip.id == trip_id)
	).scalar_one_or_none()
	if trip is None:
		raise HTTPException(status_code=404, detail="Trip not found")
	return _build_trip_read(trip)


@router.get("/trips/{trip_id}/live-location", response_model=TripLiveLocationResponse)
def get_trip_live_location(
	trip_id: UUID,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> TripLiveLocationResponse:
	if current_user.role != "passenger":
		raise HTTPException(status_code=403, detail="Only passengers can view trip live location")

	_cleanup_expired_live_locations(db)
	trip = db.get(Trip, trip_id)
	if trip is None:
		raise HTTPException(status_code=404, detail="Trip not found")

	live_location = _build_live_location(trip)
	if live_location is None:
		raise HTTPException(status_code=404, detail="Live location not available")

	return TripLiveLocationResponse(
		trip_id=trip.id,
		driver_id=trip.driver_id,
		lat=live_location.lat,
		lng=live_location.lng,
		heading=live_location.heading,
		speed_kph=live_location.speed_kph,
		updated_at=live_location.updated_at,
		expires_at=live_location.expires_at,
		auto_repeat_weekly=trip.auto_repeat_weekly,
	)


@router.put("/trips/{trip_id}/live-location", response_model=TripLiveLocationResponse)
def update_trip_live_location(
	trip_id: UUID,
	payload: TripLiveLocationUpdate,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> TripLiveLocationResponse:
	if current_user.role != "driver":
		raise HTTPException(status_code=403, detail="Only drivers can update live location")

	trip = db.get(Trip, trip_id)
	if trip is None:
		raise HTTPException(status_code=404, detail="Trip not found")
	if trip.driver_id != current_user.id:
		raise HTTPException(status_code=403, detail="You can only update your own trip")
	if trip.status != "active":
		raise HTTPException(status_code=400, detail="Live location updates allowed only for active trips")

	trip.departure_lat = payload.lat
	trip.departure_lng = payload.lng
	trip.live_heading = payload.heading
	trip.live_speed_kph = payload.speed_kph
	trip.live_location_updated_at = phnom_penh_now()
	trip.live_location_expires_at = payload.expires_at or (trip.departure_time + timedelta(hours=24))
	db.commit()
	db.refresh(trip)

	return TripLiveLocationResponse(
		trip_id=trip.id,
		driver_id=trip.driver_id,
		lat=float(trip.departure_lat),
		lng=float(trip.departure_lng),
		heading=trip.live_heading,
		speed_kph=float(trip.live_speed_kph) if trip.live_speed_kph is not None else None,
		updated_at=trip.live_location_updated_at,
		expires_at=trip.live_location_expires_at,
		auto_repeat_weekly=trip.auto_repeat_weekly,
	)


@router.post("/bookings", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
def create_booking(
	payload: BookingCreate,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> BookingRead:
	trip = db.execute(
		select(Trip)
		.options(selectinload(Trip.bookings))
		.where(Trip.id == payload.trip_id)
		.with_for_update()
	).scalar_one_or_none()
	if trip is None:
		raise HTTPException(status_code=404, detail="Trip not found")

	if current_user.role != "passenger":
		raise HTTPException(status_code=403, detail="Only passengers can create bookings")

	requested = len(payload.seat_numbers)
	if trip.status not in {"scheduled", "active"}:
		raise HTTPException(status_code=400, detail="Trip is not bookable")
	if len(set(payload.seat_numbers)) != requested:
		raise HTTPException(status_code=400, detail="seat_numbers cannot contain duplicates")
	if any(seat_number < 1 or seat_number > trip.total_seats for seat_number in payload.seat_numbers):
		raise HTTPException(status_code=400, detail="seat_numbers must be within trip seat range")
	available_seat_numbers = set(_available_seat_numbers(trip))
	unavailable_seat_numbers = sorted(set(payload.seat_numbers) - available_seat_numbers)
	if unavailable_seat_numbers:
		raise HTTPException(
			status_code=400,
			detail={
				"message": "Some requested seats are not available",
				"unavailable_seat_numbers": unavailable_seat_numbers,
				"available_seat_numbers": sorted(available_seat_numbers),
			},
		)
	if trip.available_seats < requested:
		raise HTTPException(status_code=400, detail="Not enough available seats")

	total_price = _money(_final_price_per_seat(trip) * requested)
	payment_method = _normalized_payment_method(payload.payment_method)
	if payment_method != "cash":
		_assert_digital_payment_enabled(db)
	booking = Booking(
		trip_id=payload.trip_id,
		passenger_id=current_user.id,
		seat_numbers=payload.seat_numbers,
		total_price=total_price,
		payment_method=payment_method,
		status="confirmed",
		payment_status="pending",
	)
	trip.available_seats -= requested
	db.add(booking)
	db.commit()
	db.refresh(booking)
	return BookingRead.model_validate(booking)


@router.get("/bookings", response_model=list[BookingWithTripRead])
def list_bookings(
	order: str = Query(default="desc", pattern="^(asc|desc)$"),
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> list[BookingWithTripRead]:
	sort_by_created_at = Booking.created_at.asc() if order == "asc" else Booking.created_at.desc()
	query = select(Booking).options(
		selectinload(Booking.trip).selectinload(Trip.driver),
		selectinload(Booking.trip).selectinload(Trip.vehicle),
		selectinload(Booking.trip).selectinload(Trip.bookings),
		selectinload(Booking.payment_instruction),
		selectinload(Booking.payments),
	)

	if current_user.role == "passenger":
		query = query.where(Booking.passenger_id == current_user.id)
	elif current_user.role == "driver":
		query = query.join(Trip, Booking.trip_id == Trip.id).where(Trip.driver_id == current_user.id)
	else:
		raise HTTPException(status_code=403, detail="Only passengers and drivers can access bookings")

	rows = db.execute(query.order_by(sort_by_created_at)).scalars().all()
	return [_build_booking_with_trip_read(row) for row in rows]


@router.get("/bookings/active", response_model=ActiveBookingResponse)
def get_active_booking(
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> ActiveBookingResponse:
	if current_user.role != "passenger":
		raise HTTPException(status_code=403, detail="Only passengers can access active booking")

	_cleanup_expired_live_locations(db)
	now = phnom_penh_now()
	rows = db.execute(
		select(Booking)
		.options(
			selectinload(Booking.trip).selectinload(Trip.driver),
			selectinload(Booking.trip).selectinload(Trip.vehicle),
			selectinload(Booking.trip).selectinload(Trip.bookings),
			selectinload(Booking.payment_instruction),
			selectinload(Booking.payments),
		)
		.join(Trip, Booking.trip_id == Trip.id)
		.where(
			Booking.passenger_id == current_user.id,
			Booking.status.in_(["pending", "confirmed"]),
			Trip.status.in_(["scheduled", "active"]),
			(Trip.status == "active") | (Trip.departure_time >= now),
		)
		.order_by(Trip.departure_time.asc())
	).scalars().all()
	if not rows:
		return ActiveBookingResponse(booking=None)

	active_booking = sorted(
		rows,
		key=lambda booking: (
			0 if booking.trip is not None and booking.trip.status == "active" else 1,
			booking.trip.departure_time if booking.trip is not None else booking.created_at,
		),
	)[0]
	return ActiveBookingResponse(booking=_build_booking_with_trip_read(active_booking))


@router.get("/bookings/{booking_id}", response_model=BookingWithTripRead)
def get_booking(
	booking_id: UUID,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> BookingWithTripRead:
	booking = db.execute(
		select(Booking)
		.options(
			selectinload(Booking.trip).selectinload(Trip.driver),
			selectinload(Booking.trip).selectinload(Trip.vehicle),
			selectinload(Booking.trip).selectinload(Trip.bookings),
			selectinload(Booking.payment_instruction),
			selectinload(Booking.payments),
		)
		.where(Booking.id == booking_id)
	).scalar_one_or_none()
	if booking is None:
		raise HTTPException(status_code=404, detail="Booking not found")
	trip = booking.trip
	if booking.passenger_id != current_user.id and (trip is None or trip.driver_id != current_user.id):
		raise HTTPException(status_code=403, detail="You do not have access to this booking")
	return _build_booking_with_trip_read(booking)


@router.post("/bookings/{booking_id}/driver-arrived", response_model=BookingWithTripRead)
def mark_driver_arrived(
	booking_id: UUID,
	payload: DriverArrivedRequest | None = None,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> BookingWithTripRead:
	if current_user.role != "driver":
		raise HTTPException(status_code=403, detail="Only drivers can mark arrival")

	booking = db.execute(
		select(Booking)
		.options(
			selectinload(Booking.trip).selectinload(Trip.driver),
			selectinload(Booking.trip).selectinload(Trip.vehicle),
			selectinload(Booking.trip).selectinload(Trip.bookings),
			selectinload(Booking.payment_instruction),
			selectinload(Booking.payments),
		)
		.where(Booking.id == booking_id)
	).scalar_one_or_none()
	if booking is None:
		raise HTTPException(status_code=404, detail="Booking not found")
	if booking.trip is None or booking.trip.driver_id != current_user.id:
		raise HTTPException(status_code=403, detail="You can only mark arrival for your own trip")
	if booking.status == "cancelled":
		raise HTTPException(status_code=400, detail="Cancelled bookings cannot be marked arrived")

	booking.pickup_status = "driver_arrived"
	booking.driver_arrived_at = phnom_penh_now()
	if _normalized_payment_method(booking.payment_method) != "cash":
		_assert_digital_payment_enabled(db)
		instruction = _get_or_create_payment_instruction(db, booking)
		_apply_payment_instruction_capture(instruction, payload)
		instruction.payment_status = _booking_payment_status(booking)
		booking.payment_status = instruction.payment_status
	else:
		booking.payment_status = "pending"

	db.commit()
	updated_booking = db.execute(
		select(Booking)
		.options(
			selectinload(Booking.trip).selectinload(Trip.driver),
			selectinload(Booking.trip).selectinload(Trip.vehicle),
			selectinload(Booking.trip).selectinload(Trip.bookings),
			selectinload(Booking.payment_instruction),
			selectinload(Booking.payments),
		)
		.where(Booking.id == booking_id)
	).scalar_one()
	return _build_booking_with_trip_read(updated_booking)


@router.get("/bookings/{booking_id}/payment-instruction", response_model=PaymentInstructionRead)
def get_booking_payment_instruction(
	booking_id: UUID,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> PaymentInstructionRead:
	booking = db.execute(
		select(Booking)
		.options(
			selectinload(Booking.trip),
			selectinload(Booking.payment_instruction),
			selectinload(Booking.payments),
		)
		.where(Booking.id == booking_id)
	).scalar_one_or_none()
	if booking is None:
		raise HTTPException(status_code=404, detail="Booking not found")
	trip = booking.trip
	if booking.passenger_id != current_user.id and (trip is None or trip.driver_id != current_user.id):
		raise HTTPException(status_code=403, detail="You do not have access to this booking")
	if booking.payment_instruction is None:
		return _empty_payment_instruction(booking)
	instruction = _build_payment_instruction_read(booking, booking.payment_instruction)
	if instruction is None:
		return _empty_payment_instruction(booking)
	return instruction


@router.post("/bookings/{booking_id}/passenger-boarded", response_model=BookingWithTripRead)
def mark_passenger_boarded(
	booking_id: UUID,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> BookingWithTripRead:
	if current_user.role != "driver":
		raise HTTPException(status_code=403, detail="Only drivers can mark passenger boarding")

	booking = db.execute(
		select(Booking)
		.options(
			selectinload(Booking.trip).selectinload(Trip.driver),
			selectinload(Booking.trip).selectinload(Trip.vehicle),
			selectinload(Booking.trip).selectinload(Trip.bookings),
			selectinload(Booking.payment_instruction),
			selectinload(Booking.payments),
			selectinload(Booking.wallet_entries),
		)
		.where(Booking.id == booking_id)
	).scalar_one_or_none()
	if booking is None:
		raise HTTPException(status_code=404, detail="Booking not found")
	if booking.trip is None or booking.trip.driver_id != current_user.id:
		raise HTTPException(status_code=403, detail="You can only board passengers on your own trip")
	if booking.status == "cancelled":
		raise HTTPException(status_code=400, detail="Cancelled bookings cannot be boarded")

	booking.status = "confirmed"
	booking.pickup_status = "passenger_boarded"
	db.commit()
	db.refresh(booking)
	return _build_booking_with_trip_read(booking)


@router.post("/bookings/{booking_id}/payment-instruction/upload", response_model=PaymentInstructionRead)
def upload_booking_payment_instruction_image(
	booking_id: UUID,
	payload: PaymentInstructionUploadRequest,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> PaymentInstructionRead:
	booking = db.execute(
		select(Booking)
		.options(
			selectinload(Booking.trip),
			selectinload(Booking.payment_instruction),
			selectinload(Booking.payments),
		)
		.where(Booking.id == booking_id)
	).scalar_one_or_none()
	if booking is None:
		raise HTTPException(status_code=404, detail="Booking not found")
	trip = booking.trip
	if trip is None or trip.driver_id != current_user.id:
		raise HTTPException(status_code=403, detail="Only the trip driver can upload payment instructions")
	_assert_digital_payment_enabled(db)

	image_base64 = payload.qr_image_base64.strip()
	if "," in image_base64 and image_base64.split(",", 1)[0].startswith("data:"):
		header, image_base64 = image_base64.split(",", 1)
		if ";base64" in header and payload.content_type == "image/png":
			payload.content_type = header.removeprefix("data:").removesuffix(";base64")
	try:
		b64decode(image_base64, validate=True)
	except Base64DecodeError:
		raise HTTPException(status_code=422, detail="qr_image_base64 must be valid base64")

	instruction = _get_or_create_payment_instruction(db, booking)
	instruction.source_type = "qr_image"
	instruction.qr_image_url = f"data:{payload.content_type};base64,{image_base64}"
	instruction.qr_payload = None
	instruction.deep_link_url = None
	instruction.raw_message = payload.raw_message
	instruction.parse_status = "failed"
	instruction.bank_provider = payload.bank_provider or "KHQR"
	instruction.payment_status = _booking_payment_status(booking)
	instruction.captured_at = phnom_penh_now()
	instruction.expires_at = payload.expires_at
	booking.payment_status = instruction.payment_status
	db.commit()
	db.refresh(instruction)
	return _build_payment_instruction_read(booking, instruction) or _empty_payment_instruction(booking)


@router.post("/trips/{trip_id}/complete", response_model=TripRead)
def complete_trip(
	trip_id: UUID,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> TripRead:
	if current_user.role != "driver":
		raise HTTPException(status_code=403, detail="Only drivers can complete trips")

	trip = db.execute(
		select(Trip)
		.options(selectinload(Trip.driver), selectinload(Trip.vehicle), selectinload(Trip.bookings).selectinload(Booking.wallet_entries))
		.where(Trip.id == trip_id)
	).scalar_one_or_none()
	if trip is None:
		raise HTTPException(status_code=404, detail="Trip not found")
	if trip.driver_id != current_user.id:
		raise HTTPException(status_code=403, detail="You can only complete your own trip")
	if trip.status == "completed":
		updated_trip = _load_trip_for_read(db, trip.id)
		if updated_trip is None:
			raise HTTPException(status_code=404, detail="Trip not found")
		return _build_trip_read(updated_trip)

	trip.status = "completed"
	_sync_booking_completion_from_trip(db, trip=trip)
	current_user.completed_trips = int(current_user.completed_trips or 0) + 1
	db.commit()
	updated_trip = _load_trip_for_read(db, trip.id)
	if updated_trip is None:
		raise HTTPException(status_code=404, detail="Trip not found")
	return _build_trip_read(updated_trip)


@router.patch("/bookings/{booking_id}/payment-status", response_model=BookingWithTripRead)
def update_booking_payment_status(
	booking_id: UUID,
	payload: PaymentStatusUpdate,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> BookingWithTripRead:
	booking = db.execute(
		select(Booking)
		.options(
			selectinload(Booking.trip).selectinload(Trip.driver),
			selectinload(Booking.trip).selectinload(Trip.vehicle),
			selectinload(Booking.trip).selectinload(Trip.bookings),
			selectinload(Booking.payment_instruction),
			selectinload(Booking.payments),
		)
		.where(Booking.id == booking_id)
	).scalar_one_or_none()
	if booking is None:
		raise HTTPException(status_code=404, detail="Booking not found")
	trip = booking.trip
	if booking.passenger_id != current_user.id and (trip is None or trip.driver_id != current_user.id):
		raise HTTPException(status_code=403, detail="You do not have access to this booking")

	if _normalized_payment_method(booking.payment_method) != "cash":
		_assert_digital_payment_enabled(db)

	booking.payment_status = _normalized_payment_status(payload.payment_status)
	if booking.payment_instruction is not None:
		booking.payment_instruction.payment_status = booking.payment_status

	if booking.payment_status == "paid" and booking.status != "confirmed":
		booking.status = "confirmed"
		snapshot_booking_fees(db, booking)

	db.commit()
	updated_booking = db.execute(
		select(Booking)
		.options(
			selectinload(Booking.trip).selectinload(Trip.driver),
			selectinload(Booking.trip).selectinload(Trip.vehicle),
			selectinload(Booking.trip).selectinload(Trip.bookings),
			selectinload(Booking.payment_instruction),
			selectinload(Booking.payments),
		)
		.where(Booking.id == booking_id)
	).scalar_one()
	return _build_booking_with_trip_read(updated_booking)


@router.get("/wallet/summary", response_model=WalletSummaryResponse)
def get_wallet_summary(
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> WalletSummaryResponse:
	if current_user.role not in {"passenger", "driver"}:
		raise HTTPException(status_code=403, detail="Only passengers and drivers can access wallet summary")

	if current_user.role == "driver":
		total_spent = db.execute(
			select(func.coalesce(func.sum(Booking.total_price), 0))
			.join(Trip, Booking.trip_id == Trip.id)
			.where(
				Trip.driver_id == current_user.id,
				Booking.pickup_status == "completed",
			)
		).scalar_one()
		completed_trip_count = db.execute(
			select(func.count(Booking.id))
			.join(Trip, Booking.trip_id == Trip.id)
			.where(
				Trip.driver_id == current_user.id,
				Booking.pickup_status == "completed",
			)
		).scalar_one()
		wallet = get_or_create_driver_wallet(db, driver_id=current_user.id)
		return WalletSummaryResponse(
			total_spent=float(total_spent or 0),
			currency=DEFAULT_CURRENCY,
			confirmed_payments_count=completed_trip_count,
			wallet_balance=float(wallet.total_owed_khr or 0),
			refund_total=0.0,
			promo_credit=0.0,
		)

	total_spent = db.execute(
		select(func.coalesce(func.sum(Booking.total_price), 0)).where(
			Booking.passenger_id == current_user.id,
			Booking.status == "confirmed",
		)
	).scalar_one()
	confirmed_payments_count = db.execute(
		select(func.count(Payment.id))
		.join(Booking, Payment.booking_id == Booking.id)
		.where(
			Booking.passenger_id == current_user.id,
			Payment.status == "success",
		)
	).scalar_one()
	return WalletSummaryResponse(
		total_spent=float(total_spent or 0),
		currency=DEFAULT_CURRENCY,
		confirmed_payments_count=confirmed_payments_count,
		wallet_balance=0.0,
		refund_total=0.0,
		promo_credit=0.0,
	)


@router.get("/wallet/transactions", response_model=list[WalletTransactionItem])
def list_wallet_transactions(
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> list[WalletTransactionItem]:
	if current_user.role != "passenger":
		raise HTTPException(status_code=403, detail="Only passengers can access wallet transactions")

	bookings = db.execute(
		select(Booking)
		.options(selectinload(Booking.payments), selectinload(Booking.trip))
		.where(Booking.passenger_id == current_user.id)
		.order_by(Booking.created_at.desc())
	).scalars().all()
	transactions: list[WalletTransactionItem] = []
	for booking in bookings:
		for payment in booking.payments:
			transactions.append(
				WalletTransactionItem(
					transaction_id=payment.transaction_id,
					type="payment",
					amount=float(payment.amount),
					currency=DEFAULT_CURRENCY,
					status=payment.status,
					payment_method=payment.payment_method,
					booking_id=booking.id,
					trip_id=booking.trip_id,
					created_at=payment.created_at,
				)
			)
		if not booking.payments:
			transactions.append(
				WalletTransactionItem(
					transaction_id=f"BOOKING-{booking.id}",
					type="booking",
					amount=float(booking.total_price),
					currency=DEFAULT_CURRENCY,
					status=booking.status,
					payment_method=booking.payment_method,
					booking_id=booking.id,
					trip_id=booking.trip_id,
					created_at=booking.created_at,
				)
			)
	return sorted(transactions, key=lambda transaction: transaction.created_at, reverse=True)


@router.post("/support/tickets", response_model=SupportTicketRead, status_code=status.HTTP_201_CREATED)
def create_support_ticket(
	payload: SupportTicketCreate,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> SupportTicketRead:
	if payload.user_id is not None and payload.user_id != current_user.id:
		raise HTTPException(status_code=403, detail="user_id must match the current user")

	if payload.booking_id is not None:
		booking = db.get(Booking, payload.booking_id)
		if booking is None:
			raise HTTPException(status_code=404, detail="Booking not found")
		trip = db.get(Trip, booking.trip_id)
		if booking.passenger_id != current_user.id and (trip is None or trip.driver_id != current_user.id):
			raise HTTPException(status_code=403, detail="You do not have access to this booking")

	if payload.trip_id is not None:
		trip = db.get(Trip, payload.trip_id)
		if trip is None:
			raise HTTPException(status_code=404, detail="Trip not found")
		if current_user.role == "driver" and trip.driver_id != current_user.id:
			raise HTTPException(status_code=403, detail="You do not have access to this trip")

	ticket = SupportTicket(
		user_id=current_user.id,
		booking_id=payload.booking_id,
		trip_id=payload.trip_id,
		category=payload.category,
		message=payload.message,
		passenger_location=payload.passenger_location.model_dump(mode="json", exclude_none=True) if payload.passenger_location else None,
		driver_location=payload.driver_location.model_dump(mode="json", exclude_none=True) if payload.driver_location else None,
		locale=payload.locale,
	)
	db.add(ticket)
	db.commit()
	db.refresh(ticket)
	return SupportTicketRead.model_validate(ticket)


@router.get("/support/config", response_model=SupportConfigResponse)
def get_support_config() -> SupportConfigResponse:
	return SupportConfigResponse(
		telegram_username=os.getenv("SUPPORT_TELEGRAM_USERNAME", "ride_support"),
		support_phone=os.getenv("SUPPORT_PHONE"),
		support_email=os.getenv("SUPPORT_EMAIL"),
	)


@router.get("/safety/config", response_model=SafetyConfigResponse)
def get_safety_config() -> SafetyConfigResponse:
	return SafetyConfigResponse(
		police_number=os.getenv("SAFETY_POLICE_NUMBER", "117"),
		fire_number=os.getenv("SAFETY_FIRE_NUMBER", "118"),
		ambulance_number=os.getenv("SAFETY_AMBULANCE_NUMBER", "119"),
		country_code=os.getenv("SAFETY_COUNTRY_CODE", "KH"),
	)


@router.get("/preferences/notifications", response_model=NotificationPreferencesRead)
def get_notification_preferences(
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> NotificationPreferencesRead:
	preferences = _get_or_create_notification_preferences(db, current_user)
	return NotificationPreferencesRead(
		user_id=current_user.id,
		booking_updates=preferences.booking_updates,
		route_promotions=preferences.route_promotions,
		pickup_reminders=preferences.pickup_reminders,
		updated_at=preferences.updated_at,
	)


@router.put("/preferences/notifications", response_model=NotificationPreferencesRead)
def update_notification_preferences(
	payload: NotificationPreferences,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> NotificationPreferencesRead:
	preferences = _get_or_create_notification_preferences(db, current_user)
	preferences.booking_updates = payload.booking_updates
	preferences.route_promotions = payload.route_promotions
	preferences.pickup_reminders = payload.pickup_reminders
	db.commit()
	db.refresh(preferences)
	return NotificationPreferencesRead(
		user_id=current_user.id,
		booking_updates=preferences.booking_updates,
		route_promotions=preferences.route_promotions,
		pickup_reminders=preferences.pickup_reminders,
		updated_at=preferences.updated_at,
	)


@router.post("/payments", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
def create_payment(
	payload: PaymentCreate,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> PaymentRead:
	booking = db.execute(
		select(Booking)
		.options(selectinload(Booking.payment_instruction), selectinload(Booking.payments))
		.where(Booking.id == payload.booking_id)
	).scalar_one_or_none()
	if booking is None:
		raise HTTPException(status_code=404, detail="Booking not found")
	if booking.passenger_id != current_user.id:
		raise HTTPException(status_code=403, detail="You can only pay for your own booking")
	_assert_digital_payment_enabled(db)

	existing_tx = db.execute(
		select(Payment).where(Payment.transaction_id == payload.transaction_id)
	).scalar_one_or_none()
	if existing_tx is not None:
		raise HTTPException(status_code=409, detail="transaction_id already exists")

	payment = Payment(**payload.model_dump())
	db.add(payment)
	if payload.status == "success":
		booking.payment_status = "paid"
	else:
		booking.payment_status = "pending"
	if booking.payment_instruction is not None:
		booking.payment_instruction.payment_status = booking.payment_status
	db.commit()
	db.refresh(payment)
	return PaymentRead.model_validate(payment)


@router.get("/payments/{payment_id}", response_model=PaymentRead)
def get_payment(
	payment_id: UUID,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> PaymentRead:
	payment = db.get(Payment, payment_id)
	if payment is None:
		raise HTTPException(status_code=404, detail="Payment not found")
	booking = db.get(Booking, payment.booking_id)
	trip = db.get(Trip, booking.trip_id) if booking is not None else None
	if booking is None or (
		booking.passenger_id != current_user.id and (trip is None or trip.driver_id != current_user.id)
	):
		raise HTTPException(status_code=403, detail="You do not have access to this payment")
	return PaymentRead.model_validate(payment)
