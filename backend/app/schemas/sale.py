from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SaleStatus


class SaleBase(BaseModel):
    vehicle_id: UUID
    client_id: UUID
    seller_user_id: UUID | None = None
    branch_id: UUID
    sale_price: float = Field(ge=0)
    cost: float | None = Field(default=None, ge=0)
    payment_method: str | None = Field(default=None, max_length=50)
    notes: str | None = None


class SaleCreate(SaleBase):
    sale_date: datetime | None = None


class SaleUpdate(BaseModel):
    client_id: UUID | None = None
    seller_user_id: UUID | None = None
    branch_id: UUID | None = None
    sale_date: datetime | None = None
    sale_price: float | None = Field(default=None, ge=0)
    cost: float | None = Field(default=None, ge=0)
    payment_method: str | None = Field(default=None, max_length=50)
    notes: str | None = None


class SaleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vehicle_id: UUID
    client_id: UUID
    seller_user_id: UUID | None
    branch_id: UUID
    sale_date: datetime
    sale_price: float
    cost: float | None = None
    profit: float | None = None
    payment_method: str | None = None
    status: SaleStatus
    notes: str | None = None
    created_at: datetime
