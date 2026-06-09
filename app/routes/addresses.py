from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from math import asin, cos, radians, sin, sqrt

from ..db import get_db
from ..models import Address, AddressFormEntry
from ..schemas import AddressFormCreate, AddressFormRead, AddressRead, AddressStopRead


AddressType = Literal["country", "province", "district", "commune", "village", "city", "khan", "sangkat", "ក្រុង"]
SECOND_LEVEL_TYPES = {"district", "city", "khan", "ក្រុង"}
THIRD_LEVEL_TYPES = {"commune", "sangkat"}

router = APIRouter(prefix="/addresses", tags=["addresses"])


class AddressStopResolveRequest(BaseModel):
    latitude: float
    longitude: float
    google_label: str | None = Field(default=None, max_length=255)
    google_landmark_note: str | None = Field(default=None, max_length=255)


class AddressStopResolveResponse(BaseModel):
    province: AddressRead
    district: AddressRead
    commune: AddressRead
    stop: AddressStopRead


def _ordered_addresses_query(*conditions: object):
    return (
        select(Address)
        .where(*conditions)
        .order_by(Address.description.asc(), Address.name.asc(), Address.code.asc())
    )


def _get_address_or_404(code: str, db: Session) -> Address:
    address = db.execute(select(Address).where(Address.code == code)).scalar_one_or_none()
    if address is None:
        raise HTTPException(status_code=404, detail="Address not found")
    return address


def _km_name(address: Address) -> str | None:
    return address.description or None


def _en_name(address: Address) -> str:
    return address.name


def _join_address_parts(parts: list[str | None]) -> str | None:
    joined = ", ".join(part.strip() for part in parts if part and part.strip())
    return joined or None


def _get_parent_address(address: Address, db: Session) -> Address | None:
    if not address.parent_code:
        return None
    return db.execute(select(Address).where(Address.code == address.parent_code)).scalar_one_or_none()


def _best_stop_label(address: Address) -> str:
    return address.description or address.name


def _best_stop_landmark(address: Address) -> str | None:
    return address.reference or address.official_note or address.note_by_checker or None


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    earth_radius_km = 6371.0
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return 2 * earth_radius_km * asin(sqrt(a))


def _preferred_resolved_landmark(
    address: Address,
    google_label: str | None,
    google_landmark_note: str | None,
) -> str | None:
    db_landmark = _best_stop_landmark(address)
    preferred_label = _best_stop_label(address)
    parts: list[str] = []
    for value in [db_landmark, google_landmark_note, google_label]:
        if value is None:
            continue
        cleaned = value.strip()
        if not cleaned:
            continue
        if cleaned == preferred_label:
            continue
        if cleaned not in parts:
            parts.append(cleaned)
    return ", ".join(parts) if parts else None


def _resolve_stop_from_coordinates(
    *,
    latitude: float,
    longitude: float,
    google_label: str | None,
    google_landmark_note: str | None,
    db: Session,
) -> AddressStopResolveResponse:
    villages = db.execute(
        _ordered_addresses_query(
            Address.type == "village",
            Address.latitude.is_not(None),
            Address.longitude.is_not(None),
        )
    ).scalars().all()
    if not villages:
        raise HTTPException(status_code=404, detail="No stop candidates available")

    nearest_village = min(
        villages,
        key=lambda village: _haversine_km(
            latitude,
            longitude,
            float(village.latitude),
            float(village.longitude),
        ),
    )

    commune = _get_parent_address(nearest_village, db)
    district = _get_parent_address(commune, db) if commune is not None else None
    province = _get_parent_address(district, db) if district is not None else None
    if commune is None or district is None or province is None:
        raise HTTPException(status_code=404, detail="Resolved stop is missing address hierarchy")

    stop = AddressStopRead(
        id=nearest_village.id,
        source="catalog",
        label=_best_stop_label(nearest_village),
        landmark_note=_preferred_resolved_landmark(
            nearest_village,
            google_label,
            google_landmark_note,
        ),
        latitude=float(nearest_village.latitude),
        longitude=float(nearest_village.longitude),
        commune_code=commune.code,
        commune_name=_best_stop_label(commune),
        district_code=district.code,
        district_name=_best_stop_label(district),
        province_code=province.code,
        province_name=_best_stop_label(province),
    )
    return AddressStopResolveResponse(
        province=AddressRead.model_validate(province),
        district=AddressRead.model_validate(district),
        commune=AddressRead.model_validate(commune),
        stop=stop,
    )


@router.get("/provinces", response_model=list[AddressRead])
def get_provinces(db: Session = Depends(get_db)) -> list[AddressRead]:
    return db.execute(_ordered_addresses_query(Address.type == "province")).scalars().all()


@router.get("/districts/{province_code}", response_model=list[AddressRead])
def get_districts(
    province_code: str = Path(min_length=2, max_length=20),
    db: Session = Depends(get_db),
) -> list[AddressRead]:
    province = _get_address_or_404(province_code, db)
    if province.type != "province":
        raise HTTPException(status_code=400, detail="province_code must belong to a province")
    return db.execute(
        _ordered_addresses_query(
            Address.type.in_(SECOND_LEVEL_TYPES),
            Address.parent_code == province_code,
        )
    ).scalars().all()


@router.get("/communes/{district_code}", response_model=list[AddressRead])
def get_communes(
    district_code: str = Path(min_length=3, max_length=20),
    db: Session = Depends(get_db),
) -> list[AddressRead]:
    district = _get_address_or_404(district_code, db)
    if district.type not in SECOND_LEVEL_TYPES:
        raise HTTPException(status_code=400, detail="district_code must belong to a district or city-level unit")
    return db.execute(
        _ordered_addresses_query(
            Address.type.in_(THIRD_LEVEL_TYPES),
            Address.parent_code == district_code,
        )
    ).scalars().all()


@router.get("/villages/{commune_code}", response_model=list[AddressRead])
def get_villages(
    commune_code: str = Path(min_length=5, max_length=20),
    db: Session = Depends(get_db),
) -> list[AddressRead]:
    commune = _get_address_or_404(commune_code, db)
    if commune.type != "commune":
        raise HTTPException(status_code=400, detail="commune_code must belong to a commune")
    return db.execute(
        _ordered_addresses_query(
            Address.type == "village",
            Address.parent_code == commune_code,
        )
    ).scalars().all()


@router.get("/stops/communes/{commune_code}", response_model=list[AddressStopRead])
def get_commune_stops(
    commune_code: str = Path(min_length=5, max_length=20),
    db: Session = Depends(get_db),
) -> list[AddressStopRead]:
    commune = _get_address_or_404(commune_code, db)
    if commune.type not in THIRD_LEVEL_TYPES:
        raise HTTPException(status_code=400, detail="commune_code must belong to a commune or sangkat")

    district = _get_parent_address(commune, db)
    province = _get_parent_address(district, db) if district is not None else None

    villages = db.execute(
        _ordered_addresses_query(
            Address.type == "village",
            Address.parent_code == commune_code,
        )
    ).scalars().all()

    stops: list[AddressStopRead] = []
    for village in villages:
        latitude = float(village.latitude) if village.latitude is not None else None
        longitude = float(village.longitude) if village.longitude is not None else None
        if latitude is None or longitude is None:
            continue

        stops.append(
            AddressStopRead(
                id=village.id,
                source="catalog",
                label=_best_stop_label(village),
                landmark_note=_best_stop_landmark(village),
                latitude=latitude,
                longitude=longitude,
                commune_code=commune.code,
                commune_name=_best_stop_label(commune),
                district_code=district.code if district is not None else None,
                district_name=_best_stop_label(district) if district is not None else None,
                province_code=province.code if province is not None else None,
                province_name=_best_stop_label(province) if province is not None else None,
            )
        )

    return stops


@router.post("/resolve-stop", response_model=AddressStopResolveResponse)
def resolve_stop(
    payload: AddressStopResolveRequest,
    db: Session = Depends(get_db),
) -> AddressStopResolveResponse:
    return _resolve_stop_from_coordinates(
        latitude=payload.latitude,
        longitude=payload.longitude,
        google_label=payload.google_label,
        google_landmark_note=payload.google_landmark_note,
        db=db,
    )


@router.get("/by-type/{address_type}", response_model=list[AddressRead])
def get_addresses_by_type(
    address_type: AddressType,
    db: Session = Depends(get_db),
) -> list[AddressRead]:
    return db.execute(_ordered_addresses_query(Address.type == address_type)).scalars().all()


@router.get("/by-parent/{parent_code}", response_model=list[AddressRead])
def get_addresses_by_parent(
    parent_code: str = Path(min_length=1, max_length=20),
    db: Session = Depends(get_db),
) -> list[AddressRead]:
    return db.execute(_ordered_addresses_query(Address.parent_code == parent_code)).scalars().all()


@router.get("/code/{code}", response_model=AddressRead)
def get_address_by_code(
    code: str = Path(min_length=1, max_length=20),
    db: Session = Depends(get_db),
) -> AddressRead:
    return _get_address_or_404(code, db)


@router.post("/forms", response_model=AddressFormRead, status_code=status.HTTP_201_CREATED)
def create_address_form_entry(
    payload: AddressFormCreate,
    db: Session = Depends(get_db),
) -> AddressFormRead:
    province = _get_address_or_404(payload.province_code, db)
    district = _get_address_or_404(payload.district_code, db)
    commune = _get_address_or_404(payload.commune_code, db)
    village = _get_address_or_404(payload.village_code, db)

    if province.type != "province":
        raise HTTPException(status_code=400, detail="province_code must belong to a province")
    if district.type not in SECOND_LEVEL_TYPES or district.parent_code != province.code:
        raise HTTPException(status_code=400, detail="district_code must belong to the selected province")
    if commune.type not in THIRD_LEVEL_TYPES or commune.parent_code != district.code:
        raise HTTPException(status_code=400, detail="commune_code must belong to the selected district")
    if village.type != "village" or village.parent_code != commune.code:
        raise HTTPException(status_code=400, detail="village_code must belong to the selected commune")

    country = _get_address_or_404(province.parent_code or "", db)
    if country.type != "country":
        raise HTTPException(status_code=400, detail="Selected province is missing a valid country parent")

    formatted_address_en = _join_address_parts(
        [
            payload.detail_line,
            _en_name(village),
            _en_name(commune),
            _en_name(district),
            _en_name(province),
            _en_name(country),
        ]
    )
    formatted_address_km = _join_address_parts(
        [
            payload.detail_line,
            _km_name(village),
            _km_name(commune),
            _km_name(district),
            _km_name(province),
            _km_name(country),
        ]
    )

    entry = AddressFormEntry(
        country_code=country.code,
        country_name_en=_en_name(country),
        country_name_km=_km_name(country),
        province_code=province.code,
        province_name_en=_en_name(province),
        province_name_km=_km_name(province),
        district_code=district.code,
        district_name_en=_en_name(district),
        district_name_km=_km_name(district),
        commune_code=commune.code,
        commune_name_en=_en_name(commune),
        commune_name_km=_km_name(commune),
        village_code=village.code,
        village_name_en=_en_name(village),
        village_name_km=_km_name(village),
        detail_line=payload.detail_line,
        formatted_address_en=formatted_address_en or "",
        formatted_address_km=formatted_address_km,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
