from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.branch import Branch
from app.models.client import Client
from app.models.role import Permission
from app.models.sale import Sale
from app.models.user import User
from app.models.vehicle import Vehicle
from app.services.cache_service import cache_service


class ReportService:
    """Service for generating reports with caching support"""

    async def get_dashboard_data(self) -> dict[str, int]:
        """Get dashboard summary data with caching"""
        return await cache_service.get_dashboard_data()

    async def get_inventory_summary(self) -> list[dict[str, object]]:
        """Get inventory summary with caching"""
        return await cache_service.get_inventory_summary()

    async def get_sales_summary(self) -> list[dict[str, object]]:
        """Get sales summary with caching"""
        return await cache_service.get_sales_summary()

    async def get_inventory_rows(self) -> list[dict[str, object]]:
        """Get inventory rows for export with caching"""
        return await cache_service.get_inventory_rows()

    async def get_sales_rows(self) -> list[dict[str, object]]:
        """Get sales rows for export with caching"""
        return await cache_service.get_sales_rows()


# Global report service instance
report_service = ReportService()


# Legacy functions for backward compatibility (now use cache)
def build_dashboard_payload(db: Session) -> dict[str, int]:
    vehicles_total = db.scalar(select(func.count()).select_from(Vehicle)) or 0
    branches_total = db.scalar(select(func.count()).select_from(Branch)) or 0
    clients_total = db.scalar(select(func.count()).select_from(Client)) or 0
    sales_total = db.scalar(select(func.count()).select_from(Sale)) or 0
    permissions_total = db.scalar(select(func.count()).select_from(Permission)) or 0

    return {
        "vehicles_total": int(vehicles_total),
        "branches_total": int(branches_total),
        "clients_total": int(clients_total),
        "sales_total": int(sales_total),
        "permissions_total": int(permissions_total),
    }


def build_inventory_summary(db: Session) -> list[dict[str, object]]:
    rows = db.execute(
        select(Vehicle.status, func.count(Vehicle.id).label("total"))
        .group_by(Vehicle.status)
        .order_by(Vehicle.status)
    ).all()
    return [
        {
            "status": row.status.value if hasattr(row.status, "value") else str(row.status),
            "total": int(row.total),
        }
        for row in rows
    ]


def build_sales_summary(db: Session) -> list[dict[str, object]]:
    rows = db.execute(
        select(
            Branch.name.label("branch_name"),
            func.count(Sale.id).label("sales_count"),
            func.coalesce(func.sum(Sale.sale_price), 0).label("sales_amount"),
        )
        .select_from(Sale)
        .join(Branch, Branch.id == Sale.branch_id, isouter=True)
        .group_by(Branch.name)
        .order_by(Branch.name)
    ).all()
    return [
        {
            "branch_name": row.branch_name or "Sin sucursal",
            "sales_count": int(row.sales_count),
            "sales_amount": float(row.sales_amount or 0),
        }
        for row in rows
    ]


def get_inventory_rows(db: Session) -> list[dict[str, object]]:
    rows = db.execute(
        select(
            Vehicle.id,
            Vehicle.brand,
            Vehicle.model,
            Vehicle.vehicle_year,
            Vehicle.price,
            Vehicle.mileage,
            Vehicle.vin,
            Vehicle.plate,
            Vehicle.color,
            Vehicle.transmission,
            Vehicle.fuel_type,
            Vehicle.vehicle_type,
            Vehicle.status,
            Branch.name.label("branch_name"),
        )
        .select_from(Vehicle)
        .join(Branch, Branch.id == Vehicle.branch_id, isouter=True)
        .order_by(Vehicle.created_at.desc())
    ).all()
    return [
        {
            "id": str(row.id),
            "brand": row.brand,
            "model": row.model,
            "vehicle_year": row.vehicle_year,
            "price": float(row.price),
            "mileage": row.mileage,
            "vin": row.vin,
            "plate": row.plate,
            "color": row.color,
            "transmission": row.transmission,
            "fuel_type": row.fuel_type,
            "vehicle_type": row.vehicle_type,
            "status": row.status.value if hasattr(row.status, "value") else str(row.status),
            "branch_name": row.branch_name,
        }
        for row in rows
    ]


def get_sales_rows(db: Session) -> list[dict[str, object]]:
    rows = db.execute(
        select(
            Sale.id,
            Sale.sale_date,
            Sale.sale_price,
            Sale.payment_method,
            Sale.status,
            Client.full_name.label("client_name"),
            Vehicle.brand.label("vehicle_brand"),
            Vehicle.model.label("vehicle_model"),
            Vehicle.vehicle_year.label("vehicle_year"),
            Branch.name.label("branch_name"),
        )
        .select_from(Sale)
        .join(Client, Client.id == Sale.client_id, isouter=True)
        .join(Vehicle, Vehicle.id == Sale.vehicle_id, isouter=True)
        .join(Branch, Branch.id == Sale.branch_id, isouter=True)
        .order_by(Sale.sale_date.desc())
    ).all()
    return [
        {
            "id": str(row.id),
            "sale_date": row.sale_date.isoformat() if row.sale_date else None,
            "sale_price": float(row.sale_price or 0),
            "payment_method": row.payment_method,
            "status": row.status.value if hasattr(row.status, "value") else str(row.status),
            "client_name": row.client_name or "Sin cliente",
            "vehicle": " ".join(
                str(part)
                for part in [row.vehicle_brand, row.vehicle_model, row.vehicle_year]
                if part
            ),
            "branch_name": row.branch_name or "Sin sucursal",
        }
        for row in rows
    ]
