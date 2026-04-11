from __future__ import annotations

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    vehicles_total: int
    branches_total: int
    clients_total: int
    sales_total: int
    permissions_total: int


class InventorySummaryRow(BaseModel):
    status: str
    total: int


class SalesSummaryRow(BaseModel):
    branch_name: str
    sales_count: int
    sales_amount: float


class InventoryRow(BaseModel):
    id: str
    brand: str
    model: str
    vehicle_year: int
    price: float
    mileage: int | None = None
    vin: str
    plate: str | None = None
    color: str | None = None
    transmission: str | None = None
    fuel_type: str | None = None
    vehicle_type: str | None = None
    status: str
    branch_name: str


class SalesRow(BaseModel):
    id: str
    sale_date: str | None = None
    sale_price: float
    payment_method: str | None = None
    status: str
    client_name: str
    vehicle: str
    branch_name: str
