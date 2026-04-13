from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CatalogItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    sort_order: int


class VehicleModelCatalogResponse(CatalogItemResponse):
    brand_id: UUID


class VehicleCatalogResponse(BaseModel):
    brands: list[CatalogItemResponse]
    vehicle_types: list[CatalogItemResponse]
    fuel_types: list[CatalogItemResponse]
    transmissions: list[CatalogItemResponse]
    colors: list[CatalogItemResponse]
