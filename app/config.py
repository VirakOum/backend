from dotenv import load_dotenv

import os

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://fastapi:fastapi@localhost:5432/fastapi_learning",
)


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


ENABLE_DIGITAL_PAYMENT = _env_flag("ENABLE_DIGITAL_PAYMENT", default=False)
DEFAULT_DRIVER_CASH_DEBT_LIMIT_USD = float(
    os.getenv("DEFAULT_DRIVER_CASH_DEBT_LIMIT_USD", "20"),
)
DEFAULT_DRIVER_CASH_DEBT_LIMIT_KHR = int(
    os.getenv("DEFAULT_DRIVER_CASH_DEBT_LIMIT_KHR", "80000"),
)
AUTO_LOCK_DRIVER_ON_DEBT_LIMIT = _env_flag(
    "AUTO_LOCK_DRIVER_ON_DEBT_LIMIT",
    default=True,
)
