import os

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload
from uuid import UUID
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from ..auth import get_current_user, hash_password, issue_token, verify_password
from ..db import get_db
from ..models import Booking, NotificationPreference, Payment, SupportTicket, Trip, User, Vehicle, phnom_penh_now
from ..schemas import (
	ActiveBookingResponse,
	AuthResponse,
	BookingCreate,
	BookingRead,
	BookingWithTripRead,
	LoginRequest,
	NotificationPreferences,
	NotificationPreferencesRead,
	PaymentCreate,
	PaymentRead,
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
	TripVehicleInfo,
	UserCreate,
	UserRead,
	VehicleCreate,
	VehicleRead,
	WalletSummaryResponse,
	WalletTransactionItem,
)

router = APIRouter(prefix="/travel", tags=["travel"])

BOOKING_SEAT_HOLD_STATUSES = {"pending", "confirmed"}
DEFAULT_CURRENCY = "USD"


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


def _available_seat_numbers(trip: Trip) -> list[int]:
	booked = set(_booked_seat_numbers(trip))
	open_seats = [seat_number for seat_number in range(1, trip.total_seats + 1) if seat_number not in booked]
	return open_seats[: max(0, trip.available_seats)]


def _build_trip_read(trip: Trip) -> TripRead:
	live_location = _build_live_location(trip)
	booked_seat_numbers = _booked_seat_numbers(trip)
	available_seat_numbers = _available_seat_numbers(trip)
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
		}
	)


def _build_booking_with_trip_read(booking: Booking) -> BookingWithTripRead:
	return BookingWithTripRead(
		id=booking.id,
		trip_id=booking.trip_id,
		passenger_id=booking.passenger_id,
		seat_numbers=booking.seat_numbers,
		total_price=float(booking.total_price),
		currency=DEFAULT_CURRENCY,
		payment_method=booking.payment_method,
		status=booking.status,
		created_at=booking.created_at,
		trip=_build_trip_read(booking.trip) if booking.trip is not None else None,
	)


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


@router.post("/trips", response_model=TripRead, status_code=status.HTTP_201_CREATED)
def create_trip(
	payload: TripCreate,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> TripRead:
	if current_user.role != "driver":
		raise HTTPException(status_code=403, detail="Only drivers can create trips")

	if payload.vehicle_id is not None:
		vehicle = db.get(Vehicle, payload.vehicle_id)
		if vehicle is None:
			raise HTTPException(status_code=404, detail="Vehicle not found")
		if vehicle.owner_id != current_user.id:
			raise HTTPException(status_code=403, detail="Vehicle does not belong to the current user")

	if payload.available_seats > payload.total_seats:
		raise HTTPException(status_code=400, detail="available_seats cannot exceed total_seats")

	trip_data = payload.model_dump()
	if trip_data.get("departure_lat") is not None and trip_data.get("departure_lng") is not None:
		if trip_data.get("live_location_expires_at") is None:
			trip_data["live_location_expires_at"] = payload.departure_time + timedelta(hours=24)
		trip_data["live_location_updated_at"] = phnom_penh_now()
	trip = Trip(**trip_data, driver_id=current_user.id)
	db.add(trip)
	db.commit()
	created_trip = db.execute(
		select(Trip)
		.options(selectinload(Trip.driver), selectinload(Trip.vehicle), selectinload(Trip.bookings))
		.where(Trip.id == trip.id)
	).scalar_one()
	return _build_trip_read(created_trip)


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
	booking = Booking(
		trip_id=payload.trip_id,
		passenger_id=current_user.id,
		seat_numbers=payload.seat_numbers,
		total_price=total_price,
		payment_method=payload.payment_method,
		status="pending",
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
		)
		.where(Booking.id == booking_id)
	).scalar_one_or_none()
	if booking is None:
		raise HTTPException(status_code=404, detail="Booking not found")
	trip = booking.trip
	if booking.passenger_id != current_user.id and (trip is None or trip.driver_id != current_user.id):
		raise HTTPException(status_code=403, detail="You do not have access to this booking")
	return _build_booking_with_trip_read(booking)


@router.get("/wallet/summary", response_model=WalletSummaryResponse)
def get_wallet_summary(
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> WalletSummaryResponse:
	if current_user.role != "passenger":
		raise HTTPException(status_code=403, detail="Only passengers can access wallet summary")

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
	booking = db.get(Booking, payload.booking_id)
	if booking is None:
		raise HTTPException(status_code=404, detail="Booking not found")
	if booking.passenger_id != current_user.id:
		raise HTTPException(status_code=403, detail="You can only pay for your own booking")

	existing_tx = db.execute(
		select(Payment).where(Payment.transaction_id == payload.transaction_id)
	).scalar_one_or_none()
	if existing_tx is not None:
		raise HTTPException(status_code=409, detail="transaction_id already exists")

	payment = Payment(**payload.model_dump())
	db.add(payment)
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
