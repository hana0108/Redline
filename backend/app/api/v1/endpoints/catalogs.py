from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
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
from app.schemas.catalog import (
    VehicleCatalogResponse,
    VehicleModelCatalogResponse,
)

router = APIRouter(prefix="/catalogs", tags=["catalogs"])


def _ordered_catalog_query(model):
    return (
        select(model)
        .where(model.is_active.is_(True))
        .order_by(model.sort_order.asc(), model.name.asc())
    )


@router.get("/vehicles", response_model=VehicleCatalogResponse)
def get_vehicle_catalogs(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("vehicles.read"))],
) -> VehicleCatalogResponse:
    brands = list(db.scalars(_ordered_catalog_query(VehicleBrand)).all())
    vehicle_types = list(db.scalars(_ordered_catalog_query(VehicleTypeCatalog)).all())
    fuel_types = list(db.scalars(_ordered_catalog_query(FuelTypeCatalog)).all())
    transmissions = list(db.scalars(_ordered_catalog_query(TransmissionCatalog)).all())
    colors = list(db.scalars(_ordered_catalog_query(VehicleColorCatalog)).all())

    return VehicleCatalogResponse(
        brands=brands,
        vehicle_types=vehicle_types,
        fuel_types=fuel_types,
        transmissions=transmissions,
        colors=colors,
    )


@router.get("/vehicle-models", response_model=list[VehicleModelCatalogResponse])
def get_vehicle_models(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("vehicles.read"))],
    brand_code: Annotated[str | None, Query(description="Filtrar por código de marca")] = None,
) -> list[VehicleModelCatalogResponse]:
    query = _ordered_catalog_query(VehicleModelCatalog)

    if brand_code:
        brand = db.scalar(
            select(VehicleBrand).where(
                VehicleBrand.code == brand_code, VehicleBrand.is_active.is_(True)
            )
        )
        if not brand:
            return []
        query = query.where(VehicleModelCatalog.brand_id == brand.id)

    return list(db.scalars(query).all())
