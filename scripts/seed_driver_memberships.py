from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import SessionLocal
from app.models import DriverMembership, DriverWallet, User, phnom_penh_now

MEMBERSHIP_CATALOG = {
    "normal": {
        "label": "Normal User",
        "monthly_subscription_usd": 0.0,
        "monthly_subscription_khr": 0,
        "service_fee_per_passenger_usd": 1.0,
        "service_fee_per_passenger_khr": 4000,
        "verified_badge": False,
        "priority_bookings": False,
    },
    "pro": {
        "label": "Membership Pro",
        "monthly_subscription_usd": 50.0,
        "monthly_subscription_khr": 200000,
        "service_fee_per_passenger_usd": 0.5,
        "service_fee_per_passenger_khr": 2000,
        "verified_badge": True,
        "priority_bookings": True,
    },
    "vip": {
        "label": "VIP",
        "monthly_subscription_usd": 150.0,
        "monthly_subscription_khr": 600000,
        "service_fee_per_passenger_usd": 0.25,
        "service_fee_per_passenger_khr": 1000,
        "verified_badge": True,
        "priority_bookings": True,
    },
}


def seed() -> None:
    db = SessionLocal()
    try:
        drivers = db.execute(
            select(User).where(User.role == "driver")
        ).scalars().all()

        if not drivers:
            print("No drivers found. Run `python3 scripts/seed_demo_data.py` first.")
            return

        now = phnom_penh_now()
        for driver in drivers:
            existing = db.execute(
                select(DriverMembership).where(
                    DriverMembership.driver_id == driver.id,
                    DriverMembership.status == "active",
                )
            ).scalar_one_or_none()
            if existing is not None:
                print(f"  ~ {driver.full_name}: already has active membership ({existing.code})")
                continue

            code = "normal"
            tier = MEMBERSHIP_CATALOG[code]
            membership = DriverMembership(
                driver_id=driver.id,
                code=code,
                label=tier["label"],
                status="active",
                verified_badge=tier["verified_badge"],
                priority_bookings=tier["priority_bookings"],
                monthly_subscription_usd=tier["monthly_subscription_usd"],
                monthly_subscription_khr=tier["monthly_subscription_khr"],
                service_fee_per_passenger_usd=tier["service_fee_per_passenger_usd"],
                service_fee_per_passenger_khr=tier["service_fee_per_passenger_khr"],
                started_at=now,
                next_billing_at=now + timedelta(days=30),
            )
            db.add(membership)

            existing_wallet = db.execute(
                select(DriverWallet).where(DriverWallet.driver_id == driver.id)
            ).scalar_one_or_none()
            if existing_wallet is None:
                wallet = DriverWallet(driver_id=driver.id)
                db.add(wallet)
                print(f"  + {driver.full_name}: normal membership + wallet created")
            else:
                print(f"  + {driver.full_name}: normal membership created (wallet existed)")

        db.commit()
        print(f"\nDone. {len(drivers)} driver(s) processed.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
