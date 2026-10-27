from dotenv import load_dotenv

import os

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://fastapi:fastapi@localhost:5432/fastapi_learning",
)
REDIS_URL = os.getenv("REDIS_URL", "")


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_text(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip()


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


def get_google_places_api_key() -> str:
    return _env_text("GOOGLE_PLACES_API_KEY")


def get_google_places_api_key_android() -> str:
    return _env_text("GOOGLE_PLACES_API_KEY_ANDROID") or get_google_places_api_key()


def get_google_places_api_key_ios() -> str:
    return _env_text("GOOGLE_PLACES_API_KEY_IOS") or get_google_places_api_key()


DEFAULT_GOOGLE_MAPS_API_KEY = "AIzaSyDYkud0Ul72ok5DpRMLkGhPnZekJ1-7_P4"


def get_google_maps_api_key() -> str:
    return _env_text("GOOGLE_MAPS_API_KEY") or DEFAULT_GOOGLE_MAPS_API_KEY


def get_telegram_bot_token() -> str:
    return _env_text("TELEGRAM_BOT_TOKEN")


def get_telegram_bot_username() -> str:
    return (
        _env_text("TELEGRAM_BOT_USERNAME")
        or _env_text("SUPPORT_TELEGRAM_USERNAME", "MyTravel_Taxi_bot")
    ).lstrip("@")




def get_app_env() -> str:
    return _env_text("APP_ENV", "development").lower()


def get_public_base_url() -> str:
    explicit = _env_text("PUBLIC_BASE_URL").rstrip("/")
    if explicit:
        return explicit
    env = get_app_env()
    if env in {"dev", "development", "staging"}:
        return "http://dev.mytravel.taxi"
    return "https://mytravel.taxi"
