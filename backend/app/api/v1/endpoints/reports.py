from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.report import (
    DashboardSummary,
    InventoryRow,
    InventorySummaryRow,
    SalesRow,
    SalesSummaryRow,
)
from app.services.report_service import (
    build_dashboard_payload,
    build_inventory_summary,
    build_sales_summary,
    get_inventory_rows,
    get_sales_rows,
)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/dashboard", response_model=DashboardSummary)
def get_dashboard_summary(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("reports.read"))],
) -> DashboardSummary:
    return DashboardSummary(**build_dashboard_payload(db))


@router.get("/inventory-summary", response_model=list[InventorySummaryRow])
def inventory_summary(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("reports.read"))],
) -> list[InventorySummaryRow]:
    return [InventorySummaryRow(**row) for row in build_inventory_summary(db)]


@router.get("/sales-summary", response_model=list[SalesSummaryRow])
def sales_summary(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("reports.read"))],
) -> list[SalesSummaryRow]:
    return [SalesSummaryRow(**row) for row in build_sales_summary(db)]


@router.get("/inventory-rows", response_model=list[InventoryRow])
def inventory_rows(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("reports.read"))],
) -> list[InventoryRow]:
    return [InventoryRow(**row) for row in get_inventory_rows(db)]


@router.get("/sales-rows", response_model=list[SalesRow])
def sales_rows(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("reports.read"))],
) -> list[SalesRow]:
    return [SalesRow(**row) for row in get_sales_rows(db)]
