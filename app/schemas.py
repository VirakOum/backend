from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


BookingPaymentMethod = Literal["cash", "aba", "wing"]
BookingPaymentStatus = Literal["pending", "paid", "postpaid"]
BookingPickupStatus = Literal["pending", "driver_arrived", "passenger_boarded", "completed"]
PaymentInstructionSourceType = Literal["none", "text", "manual", "qr_image", "qr_payload"]
PaymentInstructionParseStatus = Literal["missing", "parsed", "failed"]
TripRepeatMode = Literal["none", "daily", "weekly"]
TripStopSourceType = Literal["catalog", "manual_pin"]
UserNotificationType = Literal["driver_arrived", "booking_created", "boarding_requested", "boarding_confirmed"]
BoardingConfirmationStatus = Literal["none", "requested", "confirmed", "expired"]


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


class AddressStopRead(BaseModel):
    id: int | None = None
    source: TripStopSourceType = "catalog"
    label: str
    landmark_note: str | None = None
    latitude: float
    longitude: float
    commune_code: str
    commune_name: str
    district_code: str | None = None
    district_name: str | None = None
    province_code: str | None = None
    province_name: str | None = None


class TripRoutePayload(BaseModel):
    province_code: str = Field(min_length=1, max_length=20)
    province_name: str = Field(min_length=1, max_length=255)
    district_code: str = Field(min_length=1, max_length=20)
    district_name: str = Field(min_length=1, max_length=255)
    commune_code: str = Field(min_length=1, max_length=20)
    commune_name: str = Field(min_length=1, max_length=255)


class TripStopPayload(BaseModel):
    id: int | None = None
    source: TripStopSourceType
    label: str = Field(min_length=1, max_length=255)
    landmark_note: str | None = Field(default=None, max_length=255)
    latitude: float
    longitude: float
    commune_code: str = Field(min_length=1, max_length=20)
    commune_name: str = Field(min_length=1, max_length=255)
    district_code: str | None = Field(default=None, min_length=1, max_length=20)
    district_name: str | None = Field(default=None, min_length=1, max_length=255)
    province_code: str | None = Field(default=None, min_length=1, max_length=20)
    province_name: str | None = Field(default=None, min_length=1, max_length=255)


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
    device_id: str | None = Field(default=None, min_length=1, max_length=255)
    device_platform: str | None = Field(default=None, min_length=1, max_length=30)
    device_name: str | None = Field(default=None, max_length=120)


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
    device_id: str | None = Field(default=None, min_length=1, max_length=255)
    device_platform: str | None = Field(default=None, min_length=1, max_length=30)
    device_name: str | None = Field(default=None, max_length=120)


class TrustedDeviceLoginRequest(BaseModel):
    device_id: str = Field(min_length=1, max_length=255)
    device_secret: str = Field(min_length=16, max_length=255)


class TrustedDeviceAuthRead(BaseModel):
    device_secret: str
    device_platform: str
    device_name: str | None = None


class AuthResponse(BaseModel):
    token: str
    user: UserRead
    trusted_device: TrustedDeviceAuthRead | None = None


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
    departure_route: TripRoutePayload | None = None
    destination_route: TripRoutePayload | None = None
    pickup_stop: TripStopPayload | None = None
    dropoff_stop: TripStopPayload | None = None
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
    departure_route: TripRoutePayload | None = None
    destination_route: TripRoutePayload | None = None
    pickup_stop: TripStopPayload | None = None
    dropoff_stop: TripStopPayload | None = None
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
    departure_route: TripRoutePayload | None = None
    destination_route: TripRoutePayload | None = None
    pickup_stop: TripStopPayload | None = None
    dropoff_stop: TripStopPayload | None = None
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
    payment_method: BookingPaymentMethod = "cash"
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
    driver_requested_boarding_at: datetime | None = None
    passenger_confirmed_boarding_at: datetime | None = None
    boarding_confirmation_expires_at: datetime | None = None
    status: str
    created_at: datetime
    payment_instruction: PaymentInstructionRead | None = None
    model_config = ConfigDict(from_attributes=True)


class BookingWithTripRead(BookingRead):
    trip: TripRead | None = None
    passenger_contact: BookingPassengerContact | None = None
    driver_contact_phone: str | None = None
    passenger_live_location: BookingLiveLocationInfo | None = None


class BookingPassengerContact(BaseModel):
    full_name: str
    phone: str


class BookingLiveLocationInfo(BaseModel):
    lat: float
    lng: float
    accuracy_m: float | None = None
    updated_at: datetime
    expires_at: datetime


class BookingLiveLocationUpdate(BaseModel):
    lat: float
    lng: float
    accuracy_m: float | None = None


class BookingProximityRead(BaseModel):
    distance_m: float
    within_threshold: bool
    driver_location_fresh: bool
    passenger_location_fresh: bool


class BoardingConfirmationRead(BaseModel):
    status: BoardingConfirmationStatus = "none"
    driver_requested_at: datetime | None = None
    passenger_confirmed_at: datetime | None = None
    expires_at: datetime | None = None


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


class UserNotificationRead(BaseModel):
    id: UUID
    user_id: UUID
    type: UserNotificationType
    title: str
    body: str
    trip_id: UUID | None = None
    booking_id: UUID | None = None
    is_read: bool
    created_at: datetime


class UserNotificationListResponse(BaseModel):
    unread_count: int
    notifications: list[UserNotificationRead]


DriverMembershipCode = Literal["normal", "pro", "vip"]
DriverMembershipStatus = Literal["active", "expired", "cancelled", "scheduled"]
DriverInvoiceType = Literal["service_fee", "subscription"]
DriverInvoiceStatus = Literal["pending", "issued", "paid", "overdue", "failed", "void"]


class DriverMembershipSummary(BaseModel):
    code: DriverMembershipCode
    label: str
    monthly_subscription_usd: float
    monthly_subscription_khr: int
    service_fee_per_passenger_usd: float
    service_fee_per_passenger_khr: int
    verified_badge: bool = False
    priority_bookings: bool = False
    started_at: datetime | None = None
    next_billing_at: datetime | None = None
    status: DriverMembershipStatus = "active"


class DriverWalletSummary(BaseModel):
    service_fee_owed_usd: float = 0.0
    service_fee_owed_khr: int = 0
    subscription_fee_owed_usd: float = 0.0
    subscription_fee_owed_khr: int = 0
    total_owed_usd: float = 0.0
    total_owed_khr: int = 0
    credit_limit_usd: float = 0.0
    credit_limit_khr: int = 0
    is_locked: bool = False
    locked_reason: str | None = None
    last_entry_posted_at: datetime | None = None
    last_settled_at: datetime | None = None


class DriverFeeAggregate(BaseModel):
    completed_bookings: int = 0
    confirmed_passengers: int = 0
    service_fee_usd: float = 0.0
    service_fee_khr: int = 0


class DriverDailyFeeSummaryRead(BaseModel):
    date: date
    completed_bookings: int = 0
    confirmed_passengers: int = 0
    service_fee_usd: float = 0.0
    service_fee_khr: int = 0
    membership_label: str
    invoice_status: DriverInvoiceStatus = "pending"


class DriverInvoiceSummaryRead(BaseModel):
    id: UUID
    type: DriverInvoiceType
    status: DriverInvoiceStatus
    period_label: str
    total_usd: float
    total_khr: int
    issued_at: datetime | None = None
    due_at: datetime | None = None
    paid_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class DriverWalletEntryRead(BaseModel):
    entry_id: UUID
    trip_id: UUID
    booking_id: UUID
    payment_method: str
    entry_type: str
    membership_tier: str
    membership_label: str
    passenger_count: int
    cash_collected_khr: int
    service_fee_usd: float
    service_fee_khr: int
    status: str
    posted_at: datetime
    settled_at: datetime | None = None


class DriverFeeSummaryResponse(BaseModel):
    driver_id: UUID
    as_of: datetime
    timezone: str = "Asia/Phnom_Penh"
    membership: DriverMembershipSummary
    wallet: DriverWalletSummary
    today: DriverFeeAggregate
    period: DriverFeeAggregate
    daily_summaries: list[DriverDailyFeeSummaryRead]
    invoices: list[DriverInvoiceSummaryRead]
    digital_payment_enabled: bool = False
    recent_entries: list[DriverWalletEntryRead] = Field(default_factory=list)
