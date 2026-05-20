from sqlalchemy import (
    String, 
    Boolean, 
    DateTime, 
    Numeric, 
    Integer, 
    ARRAY, 
    ForeignKey,
    CheckConstraint,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from .db import Base


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
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    vehicles: Mapped[list["Vehicle"]] = relationship("Vehicle", back_populates="owner", cascade="all, delete-orphan")
    trips: Mapped[list["Trip"]] = relationship("Trip", back_populates="driver", foreign_keys="Trip.driver_id", cascade="all, delete-orphan")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="passenger", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("role IN ('passenger', 'driver')", name='role_check'),
    )


class Vehicle(Base):
    """
    Table: vehicles (ព័ត៌មានរថយន្ត)
    Vehicle information with specific seat types (4, 15, 30, 45)
    """
    __tablename__ = "vehicles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plate_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    seat_type: Mapped[int] = mapped_column(Integer, nullable=False)  # 4, 15, 30, or 45
    model: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g., Prius, Hyundai County
    company_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="vehicles")
    trips: Mapped[list["Trip"]] = relationship("Trip", back_populates="vehicle", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("seat_type IN (4, 15, 30, 45)", name='seat_type_check'),
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
    price_per_seat: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    total_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    available_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default='scheduled')  # 'scheduled', 'active', 'completed', 'cancelled'
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    driver: Mapped["User"] = relationship("User", back_populates="trips", foreign_keys=[driver_id])
    vehicle: Mapped["Vehicle | None"] = relationship("Vehicle", back_populates="trips")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="trip", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("status IN ('scheduled', 'active', 'completed', 'cancelled')", name='trip_status_check'),
        Index('idx_trips_provinces', 'departure_province', 'destination_province'),
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
    status: Mapped[str] = mapped_column(String(20), default='pending')  # 'pending', 'confirmed', 'cancelled'
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    trip: Mapped["Trip"] = relationship("Trip", back_populates="bookings")
    passenger: Mapped["User"] = relationship("User", back_populates="bookings")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="booking", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'confirmed', 'cancelled')", name='booking_status_check'),
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    booking: Mapped["Booking"] = relationship("Booking", back_populates="payments")

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'success', 'failed')", name='payment_status_check'),
    )