from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import VehicleStatus


class VehicleImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    file_path: str
    sort_order: int
    is_cover: bool
    created_at: datetime


class VehicleImageCreate(BaseModel):
    file_path: str = Field(min_length=1)
    sort_order: int = Field(default=0, ge=0)
    is_cover: bool = False


class VehicleImageSortUpdate(BaseModel):
    sort_order: int = Field(ge=0)


class VehicleBase(BaseModel):
    branch_id: UUID
    brand: str = Field(max_length=100)
    model: str = Field(max_length=100)
    vehicle_year: int = Field(ge=1900, le=2100)
    price: float = Field(ge=0)
    mileage: int = Field(ge=0, default=0)
    vin: str = Field(max_length=50)
    plate: str | None = Field(default=None, max_length=30)
    color: str | None = Field(default=None, max_length=50)
    transmission: str | None = Field(default=None, max_length=50)
    fuel_type: str | None = Field(default=None, max_length=50)
    vehicle_type: str | None = Field(default=None, max_length=50)
    description: str | None = None


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    branch_id: UUID | None = None
    brand: str | None = None
    model: str | None = None
    vehicle_year: int | None = Field(default=None, ge=1900, le=2100)
    price: float | None = Field(default=None, ge=0)
    mileage: int | None = Field(default=None, ge=0)
    plate: str | None = None
    color: str | None = None
    transmission: str | None = None
    fuel_type: str | None = None
    vehicle_type: str | None = None
    description: str | None = None


class VehicleStatusUpdate(BaseModel):
    status: VehicleStatus
    client_id: UUID | None = None
    notes: str | None = None


class PublicClientPayload(BaseModel):
    """Minimal client data captured from public site forms."""

    full_name: str = Field(min_length=2, max_length=180)
    phone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    document_type: str | None = Field(default=None, max_length=30)
    document_number: str | None = Field(default=None, max_length=50)
    notes: str | None = None


class PublicReservePayload(BaseModel):
    client: PublicClientPayload


class PublicPurchaseIntentPayload(BaseModel):
    client: PublicClientPayload


class VehicleResponse(VehicleBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: VehicleStatus
    reserved_client_id: UUID | None = None
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime
    images: list[VehicleImageResponse] = []


class VehicleStatusHistoryEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    old_status: VehicleStatus | None
    new_status: VehicleStatus
    changed_by: UUID | None
    client_id: UUID | None
    notes: str | None
    created_at: datetime
