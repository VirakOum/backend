"""add_currency_to_trips_and_bookings

Revision ID: 0030_add_currency_to_trips_and_bookings
Revises: 0029_vehicle_models
Create Date: 2026-08-28 15:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0030_add_currency_to_trips_and_bookings'
down_revision = '0029_vehicle_models'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'trips',
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='KHR'),
    )
    op.add_column(
        'bookings',
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='KHR'),
    )


def downgrade() -> None:
    op.drop_column('bookings', 'currency')
    op.drop_column('trips', 'currency')
