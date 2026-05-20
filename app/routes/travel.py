from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from uuid import UUID

from ..db import get_db
from ..models import Booking, Payment, Trip, User, Vehicle
from ..schemas import (
	BookingCreate,
	BookingRead,
	PaymentCreate,
	PaymentRead,
	TripCreate,
	TripRead,
	UserCreate,
	UserRead,
	VehicleCreate,
	VehicleRead,
)

router = APIRouter(prefix="/travel", tags=["travel"])


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserRead:
	existing = db.execute(select(User).where(User.phone == payload.phone)).scalar_one_or_none()
	if existing is not None:
		raise HTTPException(status_code=409, detail="Phone already exists")

	user = User(**payload.model_dump())
	db.add(user)
	db.commit()
	db.refresh(user)
	return UserRead.model_validate(user)


@router.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: UUID, db: Session = Depends(get_db)) -> UserRead:
	user = db.get(User, user_id)
	if user is None:
		raise HTTPException(status_code=404, detail="User not found")
	return UserRead.model_validate(user)


@router.post("/vehicles", response_model=VehicleRead, status_code=status.HTTP_201_CREATED)
def create_vehicle(payload: VehicleCreate, db: Session = Depends(get_db)) -> VehicleRead:
	owner = db.get(User, payload.owner_id)
	if owner is None:
		raise HTTPException(status_code=404, detail="Owner not found")

	existing_plate = db.execute(
		select(Vehicle).where(Vehicle.plate_number == payload.plate_number)
	).scalar_one_or_none()
	if existing_plate is not None:
		raise HTTPException(status_code=409, detail="Plate number already exists")

	vehicle = Vehicle(**payload.model_dump())
	db.add(vehicle)
	db.commit()
	db.refresh(vehicle)
	return VehicleRead.model_validate(vehicle)


@router.get("/vehicles/{vehicle_id}", response_model=VehicleRead)
def get_vehicle(vehicle_id: UUID, db: Session = Depends(get_db)) -> VehicleRead:
	vehicle = db.get(Vehicle, vehicle_id)
	if vehicle is None:
		raise HTTPException(status_code=404, detail="Vehicle not found")
	return VehicleRead.model_validate(vehicle)


@router.post("/trips", response_model=TripRead, status_code=status.HTTP_201_CREATED)
def create_trip(payload: TripCreate, db: Session = Depends(get_db)) -> TripRead:
	driver = db.get(User, payload.driver_id)
	if driver is None:
		raise HTTPException(status_code=404, detail="Driver not found")
	if driver.role != "driver":
		raise HTTPException(status_code=400, detail="User role must be driver")

	if payload.vehicle_id is not None:
		vehicle = db.get(Vehicle, payload.vehicle_id)
		if vehicle is None:
			raise HTTPException(status_code=404, detail="Vehicle not found")

	if payload.available_seats > payload.total_seats:
		raise HTTPException(status_code=400, detail="available_seats cannot exceed total_seats")

	trip = Trip(**payload.model_dump())
	db.add(trip)
	db.commit()
	db.refresh(trip)
	return TripRead.model_validate(trip)


@router.get("/trips/{trip_id}", response_model=TripRead)
def get_trip(trip_id: UUID, db: Session = Depends(get_db)) -> TripRead:
	trip = db.get(Trip, trip_id)
	if trip is None:
		raise HTTPException(status_code=404, detail="Trip not found")
	return TripRead.model_validate(trip)


@router.get("/trips/search", response_model=list[TripRead])
def search_trips(
	departure_province: str = Query(min_length=1, max_length=50),
	destination_province: str = Query(min_length=1, max_length=50),
	db: Session = Depends(get_db),
) -> list[TripRead]:
	rows = db.execute(
		select(Trip).where(
			Trip.departure_province == departure_province,
			Trip.destination_province == destination_province,
			Trip.status == "scheduled",
		)
	).scalars().all()
	return [TripRead.model_validate(row) for row in rows]


@router.post("/bookings", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
def create_booking(payload: BookingCreate, db: Session = Depends(get_db)) -> BookingRead:
	trip = db.get(Trip, payload.trip_id)
	if trip is None:
		raise HTTPException(status_code=404, detail="Trip not found")

	passenger = db.get(User, payload.passenger_id)
	if passenger is None:
		raise HTTPException(status_code=404, detail="Passenger not found")
	if passenger.role != "passenger":
		raise HTTPException(status_code=400, detail="User role must be passenger")

	requested = len(payload.seat_numbers)
	if trip.available_seats < requested:
		raise HTTPException(status_code=400, detail="Not enough available seats")

	booking = Booking(**payload.model_dump())
	trip.available_seats -= requested
	db.add(booking)
	db.commit()
	db.refresh(booking)
	return BookingRead.model_validate(booking)


@router.get("/bookings/{booking_id}", response_model=BookingRead)
def get_booking(booking_id: UUID, db: Session = Depends(get_db)) -> BookingRead:
	booking = db.get(Booking, booking_id)
	if booking is None:
		raise HTTPException(status_code=404, detail="Booking not found")
	return BookingRead.model_validate(booking)


@router.post("/payments", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)) -> PaymentRead:
	booking = db.get(Booking, payload.booking_id)
	if booking is None:
		raise HTTPException(status_code=404, detail="Booking not found")

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
def get_payment(payment_id: UUID, db: Session = Depends(get_db)) -> PaymentRead:
	payment = db.get(Payment, payment_id)
	if payment is None:
		raise HTTPException(status_code=404, detail="Payment not found")
	return PaymentRead.model_validate(payment)
