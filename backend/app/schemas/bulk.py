from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.client import ClientCreate
from app.schemas.vehicle import VehicleCreate


class BulkOperationResult(BaseModel):
    success: bool
    id: UUID | None = None
    row_number: int | None = None
    errors: list[str] = Field(default_factory=list)


class BulkOperationResponse(BaseModel):
    total_processed: int
    successful: int
    failed: int
    results: list[BulkOperationResult]


class BulkVehicleCreate(BaseModel):
    vehicles: list[VehicleCreate] = Field(..., min_length=1, max_length=100)


class BulkClientCreate(BaseModel):
    clients: list[ClientCreate] = Field(..., min_length=1, max_length=100)


class CSVImportResult(BaseModel):
    total_rows: int
    processed: int
    successful: int
    failed: int
    errors: list[dict[str, Any]]  # [{"row": 1, "errors": ["field required"]}]


class CSVImportResponse(BaseModel):
    result: CSVImportResult
    created_ids: list[UUID] = Field(default_factory=list)
