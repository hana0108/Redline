from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.db.session import get_db
from app.models.catalog import (
    FuelTypeCatalog,
    TransmissionCatalog,
    VehicleBrand,
    VehicleColorCatalog,
    VehicleModelCatalog,
    VehicleTypeCatalog,
)
from app.models.user import User
from app.models.vehicle import Vehicle

router = APIRouter(prefix="/catalogs", tags=["catalogs"])


def _catalog_to_items(rows: list) -> list[dict[str, str | int]]:
    """Convert ORM catalog rows to API dict items."""
    return [{"code": row.code, "name": row.name, "sort_order": row.sort_order} for row in rows]


def _strings_to_items(values: list[str]) -> list[dict[str, str | int]]:
    """Convert plain string list to API dict items (fallback for empty catalog tables)."""
    return [
        {"code": value, "name": value, "sort_order": idx * 10}
        for idx, value in enumerate(values, start=1)
    ]


def _get_from_catalog_or_vehicles(db: Session, catalog_model, vehicle_field) -> list[dict]:
    """Read from the catalog table; fall back to distinct Vehicle field values if empty."""
    count = db.scalar(select(func.count()).select_from(catalog_model))
    if count:
        rows = db.scalars(
            select(catalog_model)
            .where(catalog_model.is_active.is_(True))
            .order_by(catalog_model.sort_order.asc(), catalog_model.name.asc())
        ).all()
        return _catalog_to_items(list(rows))
    # Fallback: read distinct values stored in vehicles
    values = db.scalars(
        select(distinct(vehicle_field))
        .where(vehicle_field.is_not(None))
        .order_by(vehicle_field.asc())
    ).all()
    return _strings_to_items([v for v in values if v])


@router.get("/vehicles")
def get_vehicle_catalogs(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("vehicles.read"))],
) -> dict[str, list[dict[str, str | int]]]:
    brands = _get_from_catalog_or_vehicles(db, VehicleBrand, Vehicle.brand)
    vehicle_types = _get_from_catalog_or_vehicles(db, VehicleTypeCatalog, Vehicle.vehicle_type)
    fuel_types = _get_from_catalog_or_vehicles(db, FuelTypeCatalog, Vehicle.fuel_type)
    transmissions = _get_from_catalog_or_vehicles(db, TransmissionCatalog, Vehicle.transmission)
    colors = _get_from_catalog_or_vehicles(db, VehicleColorCatalog, Vehicle.color)

    return {
        "brands": brands,
        "vehicle_types": vehicle_types,
        "fuel_types": fuel_types,
        "transmissions": transmissions,
        "colors": colors,
    }


@router.get("/vehicle-models")
def get_vehicle_models(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("vehicles.read"))],
    brand_code: Annotated[str | None, Query(description="Filtrar por marca (name o code)")] = None,
) -> list[dict[str, str | int]]:
    # Try catalog tables first
    count = db.scalar(select(func.count()).select_from(VehicleModelCatalog))
    if count:
        query = (
            select(VehicleModelCatalog)
            .join(VehicleBrand, VehicleModelCatalog.brand_id == VehicleBrand.id)
            .where(VehicleModelCatalog.is_active.is_(True))
        )
        if brand_code:
            query = query.where(
                (VehicleBrand.code == brand_code) | (VehicleBrand.name == brand_code)
            )
        query = query.order_by(VehicleModelCatalog.sort_order.asc(), VehicleModelCatalog.name.asc())
        rows = db.scalars(query).all()
        return _catalog_to_items(list(rows))

    # Fallback: distinct model values from vehicles
    q = select(distinct(Vehicle.model)).where(Vehicle.model.is_not(None))
    if brand_code:
        q = q.where(Vehicle.brand == brand_code)
    q = q.order_by(Vehicle.model.asc())
    values = db.scalars(q).all()
    return _strings_to_items([v for v in values if v])
