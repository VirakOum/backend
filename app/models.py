from sqlalchemy import (
    String,
    Boolean,
    Date,
    DateTime,
    Time,
    Numeric,
    Integer,
    ARRAY,
    JSON,
    Text,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from .db import Base


def phnom_penh_now() -> datetime:
    return datetime.now(ZoneInfo("Asia/Phnom_Penh")).replace(tzinfo=None)


class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    parent_code: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    official_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    note_by_checker: Mapped[str | None] = mapped_column(Text, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    lat_lng: Mapped[str | None] = mapped_column(String(64), nullable=True)
    o_b: Mapped[str | None] = mapped_column(String(10), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "type IN ('country', 'province', 'district', 'commune', 'village', 'city', 'khan', 'sangkat', 'ក្រុង')",
            name="address_type_check",
        ),
        Index("idx_addresses_type_parent_code", "type", "parent_code"),
    )


class AddressFormEntry(Base):
    __tablename__ = "address_form_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    country_code: Mapped[str] = mapped_column(String(20), nullable=False)
    country_name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    country_name_km: Mapped[str | None] = mapped_column(String(255), nullable=True)
    province_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    province_name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    province_name_km: Mapped[str | None] = mapped_column(String(255), nullable=True)
    district_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    district_name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    district_name_km: Mapped[str | None] = mapped_column(String(255), nullable=True)
    commune_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    commune_name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    commune_name_km: Mapped[str | None] = mapped_column(String(255), nullable=True)
    village_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    village_name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    village_name_km: Mapped[str | None] = mapped_column(String(255), nullable=True)
    detail_line: Mapped[str | None] = mapped_column(String(255), nullable=True)
    formatted_address_en: Mapped[str] = mapped_column(Text, nullable=False)
    formatted_address_km: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now, onupdate=phnom_penh_now)


class User(Base):
    """
    Table: users (រក្សាទុកទិន្នន័យអ្នកប្រើប្រាស់)
    Stores both passengers and drivers differentiated by role
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'passenger' or 'driver'
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    rating_avg: Mapped[float] = mapped_column(Numeric(3, 2), default=0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    completed_trips: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now)

    # Relationships
    vehicles: Mapped[list["Vehicle"]] = relationship("Vehicle", back_populates="owner", cascade="all, delete-orphan")
    trips: Mapped[list["Trip"]] = relationship("Trip", back_populates="driver", foreign_keys="Trip.driver_id", cascade="all, delete-orphan")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="passenger", cascade="all, delete-orphan")
    auth_tokens: Mapped[list["AuthToken"]] = relationship("AuthToken", back_populates="user", cascade="all, delete-orphan")
    notification_preferences: Mapped["NotificationPreference | None"] = relationship("NotificationPreference", back_populates="user", cascade="all, delete-orphan")
    support_tickets: Mapped[list["SupportTicket"]] = relationship("SupportTicket", back_populates="user")

    __table_args__ = (
        CheckConstraint("role IN ('passenger', 'driver')", name='role_check'),
    )


class Vehicle(Base):
    """
    Table: vehicles (ព័ត៌មានរថយន្ត)
    Vehicle information with specific seat types (4, 15, 16, 23, 30, 45)
    """
    __tablename__ = "vehicles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plate_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    seat_type: Mapped[int] = mapped_column(Integer, nullable=False)  # 4, 15, 16, 23, 30, or 45
    vehicle_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g., Prius, Hyundai County
    color: Mapped[str | None] = mapped_column(String(30), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="vehicles")
    trips: Mapped[list["Trip"]] = relationship("Trip", back_populates="vehicle")

    __table_args__ = (
        CheckConstraint("seat_type IN (4, 15, 16, 23, 30, 45)", name='seat_type_check'),
    )


class Trip(Base):
    """
    Table: trips (ជើងដំណើរអន្តរខេត្ត)
    Intercounty trips created by drivers with specific departure/destination provinces
    """
    __tablename__ = "trips"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True)
    departure_province: Mapped[str] = mapped_column(String(50), nullable=False)
    destination_province: Mapped[str] = mapped_column(String(50), nullable=False)
    departure_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    departure_lat: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    departure_lng: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    departure_route: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    destination_route: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    pickup_stop: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    dropoff_stop: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    live_heading: Mapped[int | None] = mapped_column(Integer, nullable=True)
    live_speed_kph: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    live_location_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    live_location_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    repeat_mode: Mapped[str] = mapped_column(String(20), default="none")
    auto_repeat_weekly: Mapped[bool] = mapped_column(Boolean, default=False)
    recurring_day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0=Mon .. 6=Sun
    recurring_departure_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    has_return_schedule: Mapped[bool] = mapped_column(Boolean, default=False)
    return_departure_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    return_trip_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("trips.id", ondelete="SET NULL"), nullable=True)
    promotion_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    promotion_discount_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price_per_seat: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    total_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    available_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default='scheduled')  # 'scheduled', 'active', 'completed', 'cancelled'
    created_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now)

    # Relationships
    driver: Mapped["User"] = relationship("User", back_populates="trips", foreign_keys=[driver_id])
    vehicle: Mapped["Vehicle | None"] = relationship("Vehicle", back_populates="trips")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="trip", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("status IN ('scheduled', 'active', 'completed', 'cancelled')", name='trip_status_check'),
        CheckConstraint("repeat_mode IN ('none', 'daily', 'weekly')", name="trip_repeat_mode_check"),
        CheckConstraint(
            "recurring_day_of_week IS NULL OR (recurring_day_of_week >= 0 AND recurring_day_of_week <= 6)",
            name="trip_recurring_day_of_week_check",
        ),
        CheckConstraint(
            "promotion_discount_percent IS NULL OR (promotion_discount_percent >= 0 AND promotion_discount_percent <= 100)",
            name="trip_promotion_discount_percent_check",
        ),
        Index('idx_trips_provinces', 'departure_province', 'destination_province'),
        Index(
            "idx_trips_route_departure_status",
            "departure_province",
            "destination_province",
            "departure_time",
            "status",
        ),
    )


class Booking(Base):
    """
    Table: bookings (ការកក់សំបុត្ររបស់ភ្ញៀវ)
    Passenger seat reservations for trips
    """
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    passenger_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    seat_numbers: Mapped[list[int]] = mapped_column(ARRAY(Integer), nullable=False)  # e.g., [1, 2, 3]
    total_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(20), default="cash")
    payment_status: Mapped[str] = mapped_column(String(20), default="pending")
    pickup_status: Mapped[str] = mapped_column(String(30), default="pending")
    driver_arrived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='pending')  # 'pending', 'confirmed', 'cancelled'
    created_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now)

    # Fee snapshot fields (populated when booking becomes billable/completed)
    membership_code_snapshot: Mapped[str | None] = mapped_column(String(20), nullable=True)
    membership_label_snapshot: Mapped[str | None] = mapped_column(String(50), nullable=True)
    service_fee_per_passenger_usd: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    service_fee_per_passenger_khr: Mapped[int | None] = mapped_column(Integer, nullable=True)
    service_fee_total_usd: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    service_fee_total_khr: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fee_snapshotted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    settlement_summary_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Relationships
    trip: Mapped["Trip"] = relationship("Trip", back_populates="bookings")
    passenger: Mapped["User"] = relationship("User", back_populates="bookings")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="booking", cascade="all, delete-orphan")
    payment_instruction: Mapped["BookingPaymentInstruction | None"] = relationship("BookingPaymentInstruction", back_populates="booking", cascade="all, delete-orphan")
    wallet_entries: Mapped[list["DriverWalletEntry"]] = relationship(
        "DriverWalletEntry",
        back_populates="booking",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'confirmed', 'cancelled')", name='booking_status_check'),
        CheckConstraint(
            "payment_method IN ('cash', 'aba', 'wing', 'khqr', 'cash_on_arrival')",
            name="booking_payment_method_check",
        ),
        CheckConstraint(
            "payment_status IN ('pending', 'paid', 'postpaid', 'opened', 'failed', 'cancelled')",
            name="booking_payment_status_check",
        ),
        CheckConstraint("pickup_status IN ('pending', 'driver_arrived', 'passenger_boarded', 'completed')", name="booking_pickup_status_check"),
    )


class Payment(Base):
    """
    Table: payments (ប្រតិបត្តិការទូទាត់ប្រាក់)
    Payment transactions via ABA or ACLEDA
    """
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    transaction_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    payment_method: Mapped[str] = mapped_column(String(20), nullable=False)  # 'aba_payway', 'acleda_api', etc.
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default='pending')  # 'pending', 'success', 'failed'
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now)

    # Relationships
    booking: Mapped["Booking"] = relationship("Booking", back_populates="payments")

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'success', 'failed')", name='payment_status_check'),
    )


class BookingPaymentInstruction(Base):
    __tablename__ = "booking_payment_instructions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    source_type: Mapped[str] = mapped_column(String(30), default="none", nullable=False)
    deep_link_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    qr_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    qr_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    parse_status: Mapped[str] = mapped_column(String(30), default="missing", nullable=False)
    bank_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    payment_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now, onupdate=phnom_penh_now)

    booking: Mapped["Booking"] = relationship("Booking", back_populates="payment_instruction")

    __table_args__ = (
        CheckConstraint("payment_status IN ('pending', 'opened', 'paid', 'failed', 'cancelled')", name="booking_payment_instruction_payment_status_check"),
        CheckConstraint("parse_status IN ('missing', 'parsed', 'failed')", name="booking_payment_instruction_parse_status_check"),
        CheckConstraint("source_type IN ('none', 'text', 'manual', 'qr_image', 'qr_payload')", name="booking_payment_instruction_source_type_check"),
    )


class AuthToken(Base):
    __tablename__ = "auth_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now)

    user: Mapped["User"] = relationship("User", back_populates="auth_tokens")


class PassengerQuickPlace(Base):
    __tablename__ = "passenger_quick_places"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    key: Mapped[str] = mapped_column(String(20), nullable=False)
    label: Mapped[str] = mapped_column(String(50), nullable=False)
    address_line: Mapped[str] = mapped_column(String(255), nullable=False)
    lat: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False)
    lng: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now, onupdate=phnom_penh_now)

    __table_args__ = (
        UniqueConstraint("user_id", "key", name="uq_passenger_quick_places_user_key"),
    )


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    booking_updates: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    route_promotions: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    pickup_reminders: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now, onupdate=phnom_penh_now)

    user: Mapped["User"] = relationship("User", back_populates="notification_preferences")


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    booking_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True, index=True)
    trip_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("trips.id", ondelete="SET NULL"), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    passenger_location: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    driver_location: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    locale: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now)

    user: Mapped["User | None"] = relationship("User", back_populates="support_tickets")

    __table_args__ = (
        CheckConstraint("status IN ('open', 'in_progress', 'resolved', 'closed')", name="support_ticket_status_check"),
    )


class DriverMembership(Base):
    __tablename__ = "driver_memberships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    label: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    verified_badge: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    priority_bookings: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    monthly_subscription_usd: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    monthly_subscription_khr: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    service_fee_per_passenger_usd: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    service_fee_per_passenger_khr: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now, nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_billing_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now, onupdate=phnom_penh_now, nullable=False)

    __table_args__ = (
        CheckConstraint("code IN ('normal', 'pro', 'vip')", name="driver_membership_code_check"),
        CheckConstraint("status IN ('active', 'expired', 'cancelled', 'scheduled')", name="driver_membership_status_check"),
        Index("idx_driver_memberships_driver_status", "driver_id", "status", "started_at"),
    )


class DriverWallet(Base):
    __tablename__ = "driver_wallets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    service_fee_owed_usd: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    service_fee_owed_khr: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    subscription_fee_owed_usd: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    subscription_fee_owed_khr: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_owed_usd: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    total_owed_khr: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    credit_limit_usd: Mapped[float] = mapped_column(Numeric(10, 2), default=20, nullable=False)
    credit_limit_khr: Mapped[int] = mapped_column(Integer, default=80000, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    locked_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_entry_posted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_settled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now, onupdate=phnom_penh_now, nullable=False)


class DriverWalletEntry(Base):
    __tablename__ = "driver_wallet_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    trip_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    booking_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    entry_type: Mapped[str] = mapped_column(String(30), default="trip_service_fee", nullable=False)
    payment_method: Mapped[str] = mapped_column(String(20), default="cash", nullable=False)
    membership_code_snapshot: Mapped[str] = mapped_column(String(20), nullable=False)
    membership_label_snapshot: Mapped[str] = mapped_column(String(50), nullable=False)
    passenger_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    cash_collected_khr: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    service_fee_usd: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    service_fee_khr: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="owed", nullable=False)
    posted_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now, nullable=False)
    settled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now, onupdate=phnom_penh_now, nullable=False)

    booking: Mapped["Booking"] = relationship("Booking", back_populates="wallet_entries")
    trip: Mapped["Trip"] = relationship("Trip")

    __table_args__ = (
        CheckConstraint("entry_type IN ('trip_service_fee')", name="driver_wallet_entry_type_check"),
        CheckConstraint(
            "payment_method IN ('cash', 'aba', 'wing', 'khqr', 'cash_on_arrival')",
            name="driver_wallet_entry_payment_method_check",
        ),
        CheckConstraint(
            "membership_code_snapshot IN ('normal', 'pro', 'vip')",
            name="driver_wallet_entry_membership_code_check",
        ),
        CheckConstraint("status IN ('owed', 'settled', 'void')", name="driver_wallet_entry_status_check"),
        Index("idx_driver_wallet_entries_driver_posted", "driver_id", "posted_at"),
    )


class AppRuntimeSetting(Base):
    __tablename__ = "app_runtime_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    enable_digital_payment: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_lock_on_limit: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    driver_cash_debt_limit_usd: Mapped[float] = mapped_column(Numeric(10, 2), default=20, nullable=False)
    driver_cash_debt_limit_khr: Mapped[int] = mapped_column(Integer, default=80000, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now, onupdate=phnom_penh_now, nullable=False)


class DriverDailyFeeSummary(Base):
    __tablename__ = "driver_daily_fee_summaries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    membership_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("driver_memberships.id", ondelete="SET NULL"), nullable=True)
    summary_date: Mapped[date] = mapped_column(Date, nullable=False)
    membership_code: Mapped[str] = mapped_column(String(20), nullable=False)
    membership_label: Mapped[str] = mapped_column(String(50), nullable=False)
    completed_bookings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    confirmed_passengers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    service_fee_usd: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    service_fee_khr: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    invoice_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now, onupdate=phnom_penh_now, nullable=False)

    membership: Mapped["DriverMembership | None"] = relationship("DriverMembership")

    __table_args__ = (
        CheckConstraint("membership_code IN ('normal', 'pro', 'vip')", name="driver_daily_fee_membership_code_check"),
        CheckConstraint("invoice_status IN ('pending', 'issued', 'paid', 'overdue', 'failed', 'void')", name="driver_daily_fee_invoice_status_check"),
        UniqueConstraint("driver_id", "summary_date", name="uq_driver_daily_fee_driver_date"),
        Index("idx_driver_daily_fee_driver_date", "driver_id", "summary_date"),
    )


class DriverInvoice(Base):
    __tablename__ = "driver_invoices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    membership_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("driver_memberships.id", ondelete="SET NULL"), nullable=True)
    daily_summary_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("driver_daily_fee_summaries.id", ondelete="SET NULL"), nullable=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_label: Mapped[str] = mapped_column(String(100), nullable=False)
    total_usd: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    total_khr: Mapped[int] = mapped_column(Integer, nullable=False)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=phnom_penh_now, onupdate=phnom_penh_now, nullable=False)

    membership: Mapped["DriverMembership | None"] = relationship("DriverMembership")
    daily_summary: Mapped["DriverDailyFeeSummary | None"] = relationship("DriverDailyFeeSummary")

    __table_args__ = (
        CheckConstraint("type IN ('service_fee', 'subscription')", name="driver_invoice_type_check"),
        CheckConstraint("status IN ('pending', 'issued', 'paid', 'overdue', 'failed', 'void')", name="driver_invoice_status_check"),
        Index("idx_driver_invoices_driver_created", "driver_id", "created_at"),
    )
