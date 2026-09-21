from __future__ import annotations

from typing import Literal
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import AppVersionConfig, phnom_penh_now
from .schemas import AppVersionCheckResponse, AppVersionSimulateResponse

DEFAULT_VERSION_CONFIGS = {
    "android": {
        "latest_version": "1.0.0",
        "min_version": "1.0.0",
        "force_update": False,
        "update_url": "https://play.google.com/store/apps/details?id=com.mytravel.app",
        "title": "New Version Available",
        "title_km": "មានកំណែថ្មីនៃកម្មវិធី",
        "release_notes": "• Performance enhancements\n• Bug fixes and stability improvements",
        "release_notes_km": "• បង្កើនល្បឿន និងស្ថេរភាពនៃកម្មវិធី\n• កែសម្រួលចំណុចខ្វះខាតនានា",
        "is_active": True,
    },
    "ios": {
        "latest_version": "1.0.0",
        "min_version": "1.0.0",
        "force_update": False,
        "update_url": "https://apps.apple.com/app/mytravel/id000000000",
        "title": "New Version Available",
        "title_km": "មានកំណែថ្មីនៃកម្មវិធី",
        "release_notes": "• Performance enhancements\n• Bug fixes and stability improvements",
        "release_notes_km": "• បង្កើនល្បឿន និងស្ថេរភាពនៃកម្មវិធី\n• កែសម្រួលចំណុចខ្វះខាតនានា",
        "is_active": True,
    },
}


def parse_semver(v: str | None) -> tuple[int, ...]:
    if not v:
        return (0, 0, 0)
    clean = v.strip().lstrip("v").split("+")[0].split("-")[0]
    parts: list[int] = []
    for part in clean.split("."):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def get_or_create_app_version_config(db: Session, platform: str) -> AppVersionConfig:
    norm_platform = platform.lower().strip()
    if norm_platform not in ("android", "ios"):
        norm_platform = "android"

    config = db.execute(
        select(AppVersionConfig).where(AppVersionConfig.platform == norm_platform)
    ).scalar_one_or_none()

    if config is None:
        defaults = DEFAULT_VERSION_CONFIGS.get(norm_platform, DEFAULT_VERSION_CONFIGS["android"])
        config = AppVersionConfig(
            platform=norm_platform,
            latest_version=defaults["latest_version"],
            min_version=defaults["min_version"],
            force_update=defaults["force_update"],
            update_url=defaults["update_url"],
            title=defaults["title"],
            title_km=defaults["title_km"],
            release_notes=defaults["release_notes"],
            release_notes_km=defaults["release_notes_km"],
            is_active=defaults["is_active"],
            created_at=phnom_penh_now(),
            updated_at=phnom_penh_now(),
        )
        db.add(config)
        db.commit()
        db.refresh(config)

    return config


def evaluate_version(
    current_version: str | None,
    min_version: str,
    latest_version: str,
    force_update_flag: bool = False,
    is_active: bool = True,
) -> tuple[Literal["force_update", "optional_update", "continue"], str]:
    """
    App Logic:
    1. v < min -> FORCE UPDATE
    2. force_update_flag is True and v < latest -> FORCE UPDATE
    3. min <= v < latest -> OPTIONAL UPDATE
    4. v >= latest -> CONTINUE
    """
    if not is_active or not current_version:
        return ("continue", "Version control inactive or current version omitted")

    cur = parse_semver(current_version)
    min_v = parse_semver(min_version)
    lat_v = parse_semver(latest_version)

    if cur < min_v:
        return ("force_update", f"Version {current_version} is lower than minimum required version {min_version}")

    if force_update_flag and cur < lat_v:
        return ("force_update", f"Administrator enforced update to {latest_version}")

    if min_v <= cur < lat_v:
        return ("optional_update", f"New version {latest_version} available (current: {current_version})")

    return ("continue", f"App is up to date with latest version {latest_version}")


def check_version_response(
    db: Session,
    platform: str = "android",
    current_version: str | None = None,
) -> AppVersionCheckResponse:
    config = get_or_create_app_version_config(db, platform)
    action, _ = evaluate_version(
        current_version=current_version,
        min_version=config.min_version,
        latest_version=config.latest_version,
        force_update_flag=config.force_update,
        is_active=config.is_active,
    )

    return AppVersionCheckResponse(
        platform=config.platform,
        latest_version=config.latest_version,
        min_version=config.min_version,
        force_update=config.force_update,
        action=action,
        update_url=config.update_url,
        title=config.title,
        title_km=config.title_km,
        release_notes=config.release_notes,
        release_notes_km=config.release_notes_km,
        is_active=config.is_active,
    )
