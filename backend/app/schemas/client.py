from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ClientImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    file_path: str
    sort_order: int
    is_cover: bool
    created_at: datetime


class ClientImageCreate(BaseModel):
    file_path: str = Field(min_length=1)
    sort_order: int = Field(default=0, ge=0)
    is_cover: bool = False


class ClientPreferenceBase(BaseModel):
    preferred_brands: list[str] | None = None
    price_min: float | None = Field(default=None, ge=0)
    price_max: float | None = Field(default=None, ge=0)
    vehicle_type: str | None = Field(default=None, max_length=50)
    transmission: str | None = Field(default=None, max_length=50)
    fuel_type: str | None = Field(default=None, max_length=50)
    color: str | None = Field(default=None, max_length=50)
    notes: str | None = None


class ClientPreferenceResponse(ClientPreferenceBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class ClientBase(BaseModel):
    full_name: str = Field(min_length=3, max_length=180)
    document_type: str | None = Field(default=None, max_length=30)
    document_number: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    alternate_phone: str | None = Field(default=None, max_length=30)
    address: str | None = None
    notes: str | None = None


class ClientCreate(ClientBase):
    preference: ClientPreferenceBase | None = None


class ClientUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=3, max_length=180)
    document_type: str | None = Field(default=None, max_length=30)
    document_number: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    alternate_phone: str | None = Field(default=None, max_length=30)
    address: str | None = None
    notes: str | None = None
    preference: ClientPreferenceBase | None = None


class ClientResponse(ClientBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime
    preference: ClientPreferenceResponse | None = None
    images: list[ClientImageResponse] = []


class HistorySale(BaseModel):
    id: UUID
    vehicle_id: UUID
    branch_id: UUID
    sale_date: datetime
    sale_price: float
    status: str


class ClientHistoryResponse(BaseModel):
    client_id: UUID
    sales: list[HistorySale]
