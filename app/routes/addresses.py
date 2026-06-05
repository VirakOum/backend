from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Address, AddressFormEntry
from ..schemas import AddressFormCreate, AddressFormRead, AddressRead


AddressType = Literal["country", "province", "district", "commune", "village", "city", "khan", "sangkat", "ក្រុង"]
SECOND_LEVEL_TYPES = {"district", "city", "khan", "ក្រុង"}
THIRD_LEVEL_TYPES = {"commune", "sangkat"}

router = APIRouter(prefix="/addresses", tags=["addresses"])


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
