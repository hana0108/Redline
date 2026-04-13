from __future__ import annotations

import uuid

import app.db.base  # noqa: F401
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.catalog import (
    FuelTypeCatalog,
    TransmissionCatalog,
    VehicleBrand,
    VehicleColorCatalog,
    VehicleModelCatalog,
    VehicleTypeCatalog,
)

BRANDS: list[dict[str, str | int]] = [
    {"code": "toyota", "name": "Toyota", "sort_order": 10},
    {"code": "honda", "name": "Honda", "sort_order": 20},
    {"code": "ford", "name": "Ford", "sort_order": 30},
    {"code": "chevrolet", "name": "Chevrolet", "sort_order": 40},
    {"code": "hyundai", "name": "Hyundai", "sort_order": 50},
    {"code": "kia", "name": "Kia", "sort_order": 60},
    {"code": "nissan", "name": "Nissan", "sort_order": 70},
    {"code": "mazda", "name": "Mazda", "sort_order": 80},
    {"code": "volkswagen", "name": "Volkswagen", "sort_order": 90},
    {"code": "bmw", "name": "BMW", "sort_order": 100},
]

MODELS_BY_BRAND: dict[str, list[dict[str, str | int]]] = {
    "toyota": [
        {"code": "corolla", "name": "Corolla", "sort_order": 10},
        {"code": "yaris", "name": "Yaris", "sort_order": 20},
        {"code": "rav4", "name": "RAV4", "sort_order": 30},
        {"code": "hilux", "name": "Hilux", "sort_order": 40},
    ],
    "honda": [
        {"code": "civic", "name": "Civic", "sort_order": 10},
        {"code": "accord", "name": "Accord", "sort_order": 20},
        {"code": "crv", "name": "CR-V", "sort_order": 30},
        {"code": "hrv", "name": "HR-V", "sort_order": 40},
    ],
    "ford": [
        {"code": "focus", "name": "Focus", "sort_order": 10},
        {"code": "escape", "name": "Escape", "sort_order": 20},
        {"code": "explorer", "name": "Explorer", "sort_order": 30},
        {"code": "f150", "name": "F-150", "sort_order": 40},
    ],
    "chevrolet": [
        {"code": "onix", "name": "Onix", "sort_order": 10},
        {"code": "tracker", "name": "Tracker", "sort_order": 20},
        {"code": "captiva", "name": "Captiva", "sort_order": 30},
        {"code": "silverado", "name": "Silverado", "sort_order": 40},
    ],
}

VEHICLE_TYPES: list[dict[str, str | int]] = [
    {"code": "sedan", "name": "Sedan", "sort_order": 10},
    {"code": "suv", "name": "SUV", "sort_order": 20},
    {"code": "hatchback", "name": "Hatchback", "sort_order": 30},
    {"code": "pickup", "name": "Pickup", "sort_order": 40},
    {"code": "coupe", "name": "Coupe", "sort_order": 50},
    {"code": "van", "name": "Van", "sort_order": 60},
]

FUEL_TYPES: list[dict[str, str | int]] = [
    {"code": "gasolina", "name": "Gasolina", "sort_order": 10},
    {"code": "diesel", "name": "Diesel", "sort_order": 20},
    {"code": "hibrido", "name": "Hibrido", "sort_order": 30},
    {"code": "electrico", "name": "Electrico", "sort_order": 40},
]

TRANSMISSIONS: list[dict[str, str | int]] = [
    {"code": "manual", "name": "Manual", "sort_order": 10},
    {"code": "automatica", "name": "Automatica", "sort_order": 20},
    {"code": "cvt", "name": "CVT", "sort_order": 30},
]

VEHICLE_COLORS: list[dict[str, str | int]] = [
    {"code": "blanco", "name": "Blanco", "sort_order": 10},
    {"code": "negro", "name": "Negro", "sort_order": 20},
    {"code": "gris", "name": "Gris", "sort_order": 30},
    {"code": "plata", "name": "Plata", "sort_order": 40},
    {"code": "rojo", "name": "Rojo", "sort_order": 50},
    {"code": "azul", "name": "Azul", "sort_order": 60},
]


def _upsert_catalog_item(
    db: Session,
    model,
    code: str,
    name: str,
    sort_order: int,
    **extra,
):
    entity = db.scalar(select(model).where(model.code == code))
    if entity:
        changed = False
        if entity.name != name:
            entity.name = name
            changed = True
        if entity.sort_order != sort_order:
            entity.sort_order = sort_order
            changed = True
        if not entity.is_active:
            entity.is_active = True
            changed = True

        for key, value in extra.items():
            if getattr(entity, key) != value:
                setattr(entity, key, value)
                changed = True

        if changed:
            db.add(entity)
            db.flush()
        return entity

    entity = model(
        id=uuid.uuid4(),
        code=code,
        name=name,
        sort_order=sort_order,
        is_active=True,
        **extra,
    )
    db.add(entity)
    db.flush()
    return entity


def run() -> None:
    db = SessionLocal()
    try:
        inspector = inspect(db.bind)
        if not inspector.has_table("vehicle_brands", schema="redline"):
            print("Seed de catalogos omitido: tablas de catalogo no existen aun.")
            return

        brand_map: dict[str, VehicleBrand] = {}
        for item in BRANDS:
            brand = _upsert_catalog_item(
                db,
                VehicleBrand,
                code=str(item["code"]),
                name=str(item["name"]),
                sort_order=int(item["sort_order"]),
            )
            brand_map[str(item["code"])] = brand

        for brand_code, models in MODELS_BY_BRAND.items():
            brand = brand_map.get(brand_code)
            if not brand:
                continue
            for item in models:
                _upsert_catalog_item(
                    db,
                    VehicleModelCatalog,
                    code=str(item["code"]),
                    name=str(item["name"]),
                    sort_order=int(item["sort_order"]),
                    brand_id=brand.id,
                )

        for item in VEHICLE_TYPES:
            _upsert_catalog_item(
                db,
                VehicleTypeCatalog,
                code=str(item["code"]),
                name=str(item["name"]),
                sort_order=int(item["sort_order"]),
            )

        for item in FUEL_TYPES:
            _upsert_catalog_item(
                db,
                FuelTypeCatalog,
                code=str(item["code"]),
                name=str(item["name"]),
                sort_order=int(item["sort_order"]),
            )

        for item in TRANSMISSIONS:
            _upsert_catalog_item(
                db,
                TransmissionCatalog,
                code=str(item["code"]),
                name=str(item["name"]),
                sort_order=int(item["sort_order"]),
            )

        for item in VEHICLE_COLORS:
            _upsert_catalog_item(
                db,
                VehicleColorCatalog,
                code=str(item["code"]),
                name=str(item["name"]),
                sort_order=int(item["sort_order"]),
            )

        db.commit()
        print("Seed de catalogos completado correctamente.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
