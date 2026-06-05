from datetime import datetime, time
from decimal import Decimal
from uuid import UUID
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


BookingPaymentMethod = Literal["khqr", "cash_on_arrival"]
BookingPaymentStatus = Literal["pending", "opened", "paid", "failed", "cancelled"]
BookingPickupStatus = Literal["pending", "driver_arrived", "passenger_boarded", "completed"]
PaymentInstructionSourceType = Literal["none", "text", "manual", "qr_image", "qr_payload"]
PaymentInstructionParseStatus = Literal["missing", "parsed", "failed"]
TripRepeatMode = Literal["none", "daily", "weekly"]


class AddressRead(BaseModel):
    id: int
    code: str
    name: str
    description: str | None = None
    type: str
    parent_code: str | None = None
    reference: str | None = None
    official_note: str | None = None
    note_by_checker: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    lat_lng: str | None = None
    o_b: str | None = None
    model_config = ConfigDict(from_attributes=True)


class AddressFormCreate(BaseModel):
    province_code: str = Field(min_length=1, max_length=20)
    district_code: str = Field(min_length=1, max_length=20)
    commune_code: str = Field(min_length=1, max_length=20)
    village_code: str = Field(min_length=1, max_length=20)
    detail_line: str | None = Field(default=None, max_length=255)


class AddressFormRead(BaseModel):
    id: int
    country_code: str
    country_name_en: str
    country_name_km: str | None = None
    province_code: str
    province_name_en: str
    province_name_km: str | None = None
    district_code: str
    district_name_en: str
    district_name_km: str | None = None
    commune_code: str
    commune_name_en: str
    commune_name_km: str | None = None
    village_code: str
    village_name_en: str
    village_name_km: str | None = None
    detail_line: str | None = None
    formatted_address_en: str
    formatted_address_km: str | None = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


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
    rating_avg: float = 0.0
    rating_count: int = 0
    completed_trips: int = 0
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
    vehicle_type: str | None = Field(default=None, max_length=50)
    model: str | None = Field(default=None, max_length=50)
    color: str | None = Field(default=None, max_length=30)
    company_name: str | None = Field(default=None, max_length=100)


class VehicleUpdate(BaseModel):
    plate_number: str | None = Field(default=None, min_length=1, max_length=20)
    seat_type: int | None = None
    vehicle_type: str | None = Field(default=None, max_length=50)
    model: str | None = Field(default=None, max_length=50)
    color: str | None = Field(default=None, max_length=30)
    company_name: str | None = Field(default=None, max_length=100)


class VehicleRead(BaseModel):
    id: UUID
    owner_id: UUID
    plate_number: str
    seat_type: int
    vehicle_type: str | None = None
    model: str | None
    color: str | None = None
    company_name: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TripCreate(BaseModel):
    vehicle_id: UUID | None = None
    departure_province: str = Field(min_length=1, max_length=50)
    destination_province: str = Field(min_length=1, max_length=50)
    departure_time: datetime
    departure_lat: float | None = None
    departure_lng: float | None = None
    live_location_expires_at: datetime | None = None
    repeat_mode: TripRepeatMode = "none"
    auto_repeat_weekly: bool = False
    recurring_day_of_week: int | None = Field(default=None, ge=0, le=6)
    recurring_departure_time: time | None = None
    has_return_schedule: bool = False
    return_departure_time: datetime | None = None
    promotion_label: str | None = Field(default=None, max_length=50)
    promotion_discount_percent: int | None = Field(default=None, ge=0, le=100)
    price_per_seat: Decimal = Field(gt=0)
    total_seats: int = Field(gt=0)
    available_seats: int = Field(ge=0)
    status: str = Field(default="scheduled", pattern="^(scheduled|active|completed|cancelled)$")


class TripUpdate(BaseModel):
    vehicle_id: UUID | None = None
    departure_province: str | None = Field(default=None, min_length=1, max_length=50)
    destination_province: str | None = Field(default=None, min_length=1, max_length=50)
    departure_time: datetime | None = None
    departure_lat: float | None = None
    departure_lng: float | None = None
    live_location_expires_at: datetime | None = None
    repeat_mode: TripRepeatMode | None = None
    auto_repeat_weekly: bool | None = None
    recurring_day_of_week: int | None = Field(default=None, ge=0, le=6)
    recurring_departure_time: time | None = None
    has_return_schedule: bool | None = None
    return_departure_time: datetime | None = None
    promotion_label: str | None = Field(default=None, max_length=50)
    promotion_discount_percent: int | None = Field(default=None, ge=0, le=100)
    price_per_seat: Decimal | None = Field(default=None, gt=0)
    total_seats: int | None = Field(default=None, gt=0)
    available_seats: int | None = Field(default=None, ge=0)
    status: str | None = Field(default=None, pattern="^(scheduled|active|completed|cancelled)$")


class TripDriverInfo(BaseModel):
    id: UUID
    full_name: str
    avatar_url: str | None = None
    is_verified: bool
    rating_avg: float
    rating_count: int
    completed_trips: int
    model_config = ConfigDict(from_attributes=True)


class TripVehicleInfo(BaseModel):
    id: UUID
    type: str | None = None
    model: str | None = None
    plate_number: str
    color: str | None = None
    seat_type: int
    model_config = ConfigDict(from_attributes=True)


class TripPromotionInfo(BaseModel):
    label: str
    discount_percent: int
    original_price_per_seat: float
    final_price_per_seat: float
    currency: str = "USD"


class TripLiveLocationInfo(BaseModel):
    lat: float
    lng: float
    heading: int | None = None
    speed_kph: float | None = None
    updated_at: datetime | None = None
    expires_at: datetime


class TripRead(BaseModel):
    id: UUID
    driver_id: UUID
    vehicle_id: UUID | None
    departure_province: str
    destination_province: str
    departure_time: datetime
    departure_lat: float | None
    departure_lng: float | None
    live_lat: float | None = None
    live_lng: float | None = None
    live_heading: int | None
    live_speed_kph: float | None
    live_location_updated_at: datetime | None
    live_location_expires_at: datetime | None
    repeat_mode: TripRepeatMode = "none"
    auto_repeat_weekly: bool
    recurring_day_of_week: int | None
    recurring_departure_time: time | None
    has_return_schedule: bool = False
    return_departure_time: datetime | None = None
    return_trip_id: UUID | None = None
    price_per_seat: float
    currency: str = "USD"
    total_seats: int
    available_seats: int
    booked_seat_numbers: list[int] = Field(default_factory=list)
    available_seat_numbers: list[int] = Field(default_factory=list)
    appBookedSeatCount: int = 0
    appBookingCount: int = 0
    status: str
    created_at: datetime
    driver: TripDriverInfo | None = None
    vehicle: TripVehicleInfo | None = None
    promotion: TripPromotionInfo | None = None
    live_location: TripLiveLocationInfo | None = None
    model_config = ConfigDict(from_attributes=True)


class BookingCreate(BaseModel):
    trip_id: UUID
    seat_numbers: list[int] = Field(min_length=1)
    payment_method: BookingPaymentMethod = "cash_on_arrival"
    total_price: Decimal | None = Field(default=None, gt=0)
    status: str = Field(default="pending", pattern="^(pending|confirmed|cancelled)$")


class PaymentInstructionRead(BaseModel):
    booking_id: UUID
    trip_id: UUID | None = None
    source_type: PaymentInstructionSourceType = "none"
    deep_link_url: str | None = None
    qr_image_url: str | None = None
    qr_payload: str | None = None
    raw_message: str | None = None
    parse_status: PaymentInstructionParseStatus = "missing"
    bank_provider: str | None = None
    payment_status: BookingPaymentStatus = "pending"
    captured_at: datetime | None = None
    expires_at: datetime | None = None


class DriverArrivedRequest(BaseModel):
    source_type: PaymentInstructionSourceType | None = None
    deep_link_url: str | None = Field(default=None, max_length=1000)
    qr_image_url: str | None = Field(default=None, max_length=1000)
    qr_payload: str | None = None
    raw_message: str | None = None
    bank_provider: str | None = Field(default=None, max_length=50)
    expires_at: datetime | None = None


class PaymentInstructionUploadRequest(BaseModel):
    qr_image_base64: str = Field(min_length=1)
    content_type: str = Field(default="image/png", max_length=100)
    raw_message: str | None = None
    bank_provider: str | None = Field(default=None, max_length=50)
    expires_at: datetime | None = None


class PaymentStatusUpdate(BaseModel):
    payment_status: BookingPaymentStatus


class BookingRead(BaseModel):
    id: UUID
    trip_id: UUID
    passenger_id: UUID
    seat_numbers: list[int]
    total_price: float
    currency: str = "USD"
    payment_method: BookingPaymentMethod
    payment_status: BookingPaymentStatus = "pending"
    pickup_status: BookingPickupStatus = "pending"
    driver_arrived_at: datetime | None = None
    status: str
    created_at: datetime
    payment_instruction: PaymentInstructionRead | None = None
    model_config = ConfigDict(from_attributes=True)


class BookingWithTripRead(BookingRead):
    trip: TripRead | None = None


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
    amount: float
    currency: str = "USD"
    status: str
    paid_at: datetime | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PassengerPlaceUpsert(BaseModel):
    address_line: str = Field(min_length=1, max_length=255)
    lat: float
    lng: float
    note: str | None = Field(default=None, max_length=255)


class PassengerPlaceItem(BaseModel):
    key: str
    label: str
    address_id: str | None
    address_line: str | None
    has_address: bool


class PassengerPlacesResponse(BaseModel):
    places: list[PassengerPlaceItem]


class ScheduleOption(BaseModel):
    id: str
    label: str


class ScheduleBucketRange(BaseModel):
    id: Literal["morning", "afternoon", "evening"]
    start: str
    end: str


class RideChoiceOption(BaseModel):
    id: str
    title: str
    meta: str
    icon: str
    color: str
    seat_type: int | None = None
    is_more: bool = False


class TripSearchConfigResponse(BaseModel):
    default_schedule: str
    schedule_options: list[ScheduleOption]
    ride_choices: list[RideChoiceOption]
    timezone: str
    schedule_bucket_ranges: list[ScheduleBucketRange]


class NearbyDriverItem(BaseModel):
    trip_id: UUID
    driver_id: UUID
    lat: float
    lng: float
    heading: int | None = None
    speed_kph: float | None = None
    seat_type: int
    total_seats: int
    available_seats: int
    updated_at: datetime | None = None
    expires_at: datetime
    auto_repeat_weekly: bool


class NearbyDriversResponse(BaseModel):
    drivers: list[NearbyDriverItem]


class TripLiveLocationUpdate(BaseModel):
    lat: float
    lng: float
    heading: int | None = Field(default=None, ge=0, le=360)
    speed_kph: float | None = Field(default=None, ge=0)
    expires_at: datetime | None = None


class TripLiveLocationResponse(BaseModel):
    trip_id: UUID
    driver_id: UUID
    lat: float
    lng: float
    heading: int | None = None
    speed_kph: float | None = None
    updated_at: datetime | None = None
    expires_at: datetime
    auto_repeat_weekly: bool


class ActiveBookingResponse(BaseModel):
    booking: BookingWithTripRead | None = None


class WalletSummaryResponse(BaseModel):
    total_spent: float
    currency: str = "USD"
    confirmed_payments_count: int
    wallet_balance: float = 0.0
    refund_total: float = 0.0
    promo_credit: float = 0.0


class WalletTransactionItem(BaseModel):
    transaction_id: str
    type: str
    amount: float
    currency: str = "USD"
    status: str
    payment_method: str
    booking_id: UUID
    trip_id: UUID
    created_at: datetime


class SupportLocation(BaseModel):
    lat: float | None = None
    lng: float | None = None
    heading: int | None = None
    speed_kph: float | None = None
    updated_at: datetime | None = None
    address: str | None = None
    extra: dict[str, Any] | None = None


class SupportTicketCreate(BaseModel):
    category: str = Field(min_length=1, max_length=50)
    message: str = Field(min_length=1)
    user_id: UUID | None = None
    booking_id: UUID | None = None
    trip_id: UUID | None = None
    passenger_location: SupportLocation | None = None
    driver_location: SupportLocation | None = None
    locale: str | None = Field(default=None, max_length=20)


class SupportTicketRead(BaseModel):
    id: UUID
    category: str
    message: str
    user_id: UUID | None
    booking_id: UUID | None
    trip_id: UUID | None
    passenger_location: dict[str, Any] | None
    driver_location: dict[str, Any] | None
    locale: str | None
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SupportConfigResponse(BaseModel):
    telegram_username: str
    support_phone: str | None = None
    support_email: str | None = None


class SafetyConfigResponse(BaseModel):
    police_number: str
    fire_number: str
    ambulance_number: str
    country_code: str


class NotificationPreferences(BaseModel):
    booking_updates: bool = True
    route_promotions: bool = True
    pickup_reminders: bool = True


class NotificationPreferencesRead(NotificationPreferences):
    user_id: UUID
    updated_at: datetime | None = None
