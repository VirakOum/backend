from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100, examples=["Notebook"])
    description: str | None = Field(default=None, max_length=300)


class ItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=300)


class ItemRead(ItemCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    phone: str = Field(min_length=6, max_length=20)
    full_name: str = Field(min_length=1, max_length=100)
    role: str = Field(pattern="^(passenger|driver)$")
    password: str = Field(min_length=8, max_length=128)
    avatar_url: str | None = None


class UserRead(BaseModel):
    id: UUID
    phone: str
    full_name: str
    role: str
    avatar_url: str | None
    is_verified: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    phone: str = Field(min_length=6, max_length=20)
    password: str = Field(min_length=8, max_length=128)


class AuthResponse(BaseModel):
    token: str
    user: UserRead


class VehicleCreate(BaseModel):
    plate_number: str = Field(min_length=1, max_length=20)
    seat_type: int
    model: str | None = Field(default=None, max_length=50)
    company_name: str | None = Field(default=None, max_length=100)


class VehicleRead(BaseModel):
    id: UUID
    owner_id: UUID
    plate_number: str
    seat_type: int
    model: str | None
    company_name: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TripCreate(BaseModel):
    vehicle_id: UUID | None = None
    departure_province: str = Field(min_length=1, max_length=50)
    destination_province: str = Field(min_length=1, max_length=50)
    departure_time: datetime
    price_per_seat: Decimal = Field(gt=0)
    total_seats: int = Field(gt=0)
    available_seats: int = Field(ge=0)
    status: str = Field(default="scheduled", pattern="^(scheduled|active|completed|cancelled)$")


class TripRead(BaseModel):
    id: UUID
    driver_id: UUID
    vehicle_id: UUID | None
    departure_province: str
    destination_province: str
    departure_time: datetime
    price_per_seat: Decimal
    total_seats: int
    available_seats: int
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class BookingCreate(BaseModel):
    trip_id: UUID
    seat_numbers: list[int] = Field(min_length=1)
    total_price: Decimal = Field(gt=0)
    status: str = Field(default="pending", pattern="^(pending|confirmed|cancelled)$")


class BookingRead(BaseModel):
    id: UUID
    trip_id: UUID
    passenger_id: UUID
    seat_numbers: list[int]
    total_price: Decimal
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PaymentCreate(BaseModel):
    booking_id: UUID
    transaction_id: str = Field(min_length=1, max_length=100)
    payment_method: str = Field(min_length=1, max_length=20)
    amount: Decimal = Field(gt=0)
    status: str = Field(default="pending", pattern="^(pending|success|failed)$")
    paid_at: datetime | None = None


class PaymentRead(BaseModel):
    id: UUID
    booking_id: UUID
    transaction_id: str
    payment_method: str
    amount: Decimal
    status: str
    paid_at: datetime | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
