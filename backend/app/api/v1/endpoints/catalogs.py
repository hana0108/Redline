from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import distinct, select
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.models.vehicle import Vehicle

router = APIRouter(prefix="/catalogs", tags=["catalogs"])


def _to_items(values: list[str]) -> list[dict[str, str | int]]:
    items: list[dict[str, str | int]] = []
    for idx, value in enumerate(values, start=1):
        items.append({"code": value, "name": value, "sort_order": idx * 10})
    return items


@router.get("/vehicles")
def get_vehicle_catalogs(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("vehicles.read"))],
) -> dict[str, list[dict[str, str | int]]]:
    brands = list(
        db.scalars(
            select(distinct(Vehicle.brand))
            .where(Vehicle.brand.is_not(None))
            .order_by(Vehicle.brand.asc())
        ).all()
    )
    vehicle_types = list(
        db.scalars(
            select(distinct(Vehicle.vehicle_type))
            .where(Vehicle.vehicle_type.is_not(None))
            .order_by(Vehicle.vehicle_type.asc())
        ).all()
    )
    fuel_types = list(
        db.scalars(
            select(distinct(Vehicle.fuel_type))
            .where(Vehicle.fuel_type.is_not(None))
            .order_by(Vehicle.fuel_type.asc())
        ).all()
    )
    transmissions = list(
        db.scalars(
            select(distinct(Vehicle.transmission))
            .where(Vehicle.transmission.is_not(None))
            .order_by(Vehicle.transmission.asc())
        ).all()
    )
    colors = list(
        db.scalars(
            select(distinct(Vehicle.color))
            .where(Vehicle.color.is_not(None))
            .order_by(Vehicle.color.asc())
        ).all()
    )

    return {
        "brands": _to_items([item for item in brands if item]),
        "vehicle_types": _to_items([item for item in vehicle_types if item]),
        "fuel_types": _to_items([item for item in fuel_types if item]),
        "transmissions": _to_items([item for item in transmissions if item]),
        "colors": _to_items([item for item in colors if item]),
    }


@router.get("/vehicle-models")
def get_vehicle_models(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("vehicles.read"))],
    brand_code: Annotated[str | None, Query(description="Filtrar por marca")] = None,
) -> list[dict[str, str | int]]:
    query = select(distinct(Vehicle.model)).where(Vehicle.model.is_not(None))
    if brand_code:
        query = query.where(Vehicle.brand == brand_code)
    query = query.order_by(Vehicle.model.asc())

    values = list(db.scalars(query).all())
    return _to_items([item for item in values if item])
