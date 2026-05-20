"""Create rideshare tables: users, vehicles, trips, bookings, payments

Revision ID: 0002_create_rideshare_tables
Revises: 7d4b042c53f1_create_category_table
Create Date: 2026-05-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0002_create_rideshare_tables'
down_revision = '7d4b042c53f1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable uuid-ossp extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Create USERS table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('full_name', sa.String(100), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("role IN ('passenger', 'driver')", name='role_check'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('phone'),
    )
    op.create_index('ix_users_phone', 'users', ['phone'])

    # Create VEHICLES table
    op.create_table(
        'vehicles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plate_number', sa.String(20), nullable=False),
        sa.Column('seat_type', sa.Integer(), nullable=False),
        sa.Column('model', sa.String(50), nullable=True),
        sa.Column('company_name', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('seat_type IN (4, 15, 30, 45)', name='seat_type_check'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plate_number'),
    )
    op.create_index('ix_vehicles_plate_number', 'vehicles', ['plate_number'])

    # Create TRIPS table
    op.create_table(
        'trips',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('driver_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('vehicle_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('departure_province', sa.String(50), nullable=False),
        sa.Column('destination_province', sa.String(50), nullable=False),
        sa.Column('departure_time', sa.DateTime(), nullable=False),
        sa.Column('price_per_seat', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('total_seats', sa.Integer(), nullable=False),
        sa.Column('available_seats', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='scheduled'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('scheduled', 'active', 'completed', 'cancelled')", name='trip_status_check'),
        sa.ForeignKeyConstraint(['driver_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_trips_provinces', 'trips', ['departure_province', 'destination_province'])

    # Create BOOKINGS table
    op.create_table(
        'bookings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('trip_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('passenger_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('seat_numbers', sa.ARRAY(sa.Integer()), nullable=False),
        sa.Column('total_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('pending', 'confirmed', 'cancelled')", name='booking_status_check'),
        sa.ForeignKeyConstraint(['passenger_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create PAYMENTS table
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('booking_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transaction_id', sa.String(100), nullable=False),
        sa.Column('payment_method', sa.String(20), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('pending', 'success', 'failed')", name='payment_status_check'),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transaction_id'),
    )
    op.create_index('ix_payments_transaction_id', 'payments', ['transaction_id'])


def downgrade() -> None:
    # Drop indices
    op.drop_index('ix_payments_transaction_id', table_name='payments')
    op.drop_index('idx_trips_provinces', table_name='trips')
    op.drop_index('ix_vehicles_plate_number', table_name='vehicles')
    op.drop_index('ix_users_phone', table_name='users')

    # Drop tables in reverse order
    op.drop_table('payments')
    op.drop_table('bookings')
    op.drop_table('trips')
    op.drop_table('vehicles')
    op.drop_table('users')
