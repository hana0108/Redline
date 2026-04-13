from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.core.exceptions import conflict
from app.db.session import get_db
from app.models.branch import Branch
from app.models.client import Client
from app.models.enums import AuditAction, SaleStatus, VehicleStatus
from app.models.sale import Sale
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.sale import SaleCreate, SaleResponse, SaleUpdate
from app.services.audit import add_audit_log
from app.services.cache_service import cache_service
from app.services.commercial_service import ensure_vehicle_sellable, get_sale_or_404, validate_commercial_refs
from app.services.pdf_generator import build_sale_pdf
from app.services.response_service import stream_pdf
from app.services.settings_service import get_company_info

router = APIRouter(prefix="/sales", tags=["sales"])


@router.get("", response_model=list[SaleResponse])
def list_sales(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("sales.read"))],
    branch_id: UUID | None = None,
    seller_user_id: UUID | None = None,
    client_id: UUID | None = None,
) -> list[Sale]:
    query = select(Sale).order_by(Sale.sale_date.desc())
    if branch_id:
        query = query.where(Sale.branch_id == branch_id)
    if seller_user_id:
        query = query.where(Sale.seller_user_id == seller_user_id)
    if client_id:
        query = query.where(Sale.client_id == client_id)
    return list(db.scalars(query).all())


@router.post("", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
async def create_sale(
    payload: SaleCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("sales.write"))],
) -> Sale:
    refs = validate_commercial_refs(
        db,
        vehicle_id=payload.vehicle_id,
        client_id=payload.client_id,
        branch_id=payload.branch_id,
        seller_user_id=payload.seller_user_id,
    )
    ensure_vehicle_sellable(db, refs.vehicle)

    sale = Sale(
        vehicle_id=payload.vehicle_id,
        client_id=payload.client_id,
        seller_user_id=payload.seller_user_id,
        branch_id=payload.branch_id,
        sale_date=payload.sale_date or datetime.now(),
        sale_price=payload.sale_price,
        cost=payload.cost,
        profit=(payload.sale_price - payload.cost) if payload.cost is not None else None,
        payment_method=payload.payment_method,
        status=SaleStatus.COMPLETADA,
        notes=payload.notes,
    )
    db.add(sale)
    refs.vehicle.status = VehicleStatus.VENDIDO
    db.flush()

    add_audit_log(
        db,
        action=AuditAction.SALE,
        entity_type="sales",
        entity_id=sale.id,
        user_id=current_user.id,
        new_data={
            "vehicle_id": str(payload.vehicle_id),
            "client_id": str(payload.client_id),
            "branch_id": str(payload.branch_id) if payload.branch_id else None,
            "sale_price": float(payload.sale_price),
        },
    )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="No fue posible registrar la venta") from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    db.refresh(sale)

    # Invalidate related caches after successful creation
    await cache_service.invalidate_sale_related_caches()
    await cache_service.invalidate_vehicle_related_caches(str(payload.vehicle_id))
    await cache_service.invalidate_client_related_caches(str(payload.client_id))

    return sale


@router.patch("/{sale_id}", response_model=SaleResponse)
async def update_sale(
    sale_id: UUID,
    payload: SaleUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("sales.write"))],
) -> Sale:
    sale = get_sale_or_404(db, sale_id)
    update_data = payload.model_dump(exclude_unset=True)

    if "client_id" in update_data and update_data["client_id"] != sale.client_id:
        client = db.get(Client, update_data["client_id"])
        if not client:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

    if "branch_id" in update_data and update_data["branch_id"] != sale.branch_id:
        branch = db.get(Branch, update_data["branch_id"])
        if not branch:
            raise HTTPException(status_code=404, detail="Sucursal no encontrada")

    if "seller_user_id" in update_data and update_data["seller_user_id"]:
        seller = db.get(User, update_data["seller_user_id"])
        if not seller:
            raise HTTPException(status_code=404, detail="Vendedor no encontrado")

    old_data = {
        "client_id": str(sale.client_id),
        "seller_user_id": str(sale.seller_user_id) if sale.seller_user_id else None,
        "branch_id": str(sale.branch_id) if sale.branch_id else None,
        "sale_date": sale.sale_date.isoformat() if sale.sale_date else None,
        "sale_price": float(sale.sale_price),
        "cost": float(sale.cost) if sale.cost is not None else None,
        "payment_method": sale.payment_method,
        "notes": sale.notes,
    }

    for field, value in update_data.items():
        setattr(sale, field, value)

    if "sale_price" in update_data or "cost" in update_data:
        sale.profit = (sale.sale_price - sale.cost) if sale.cost is not None else None

    add_audit_log(
        db,
        action=AuditAction.UPDATE,
        entity_type="sales",
        entity_id=sale.id,
        user_id=current_user.id,
        old_data=old_data,
        new_data=update_data,
    )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="No fue posible actualizar la venta") from exc

    db.refresh(sale)

    # Invalidate related caches after successful update
    await cache_service.invalidate_sale_related_caches()
    await cache_service.invalidate_vehicle_related_caches(str(sale.vehicle_id))
    await cache_service.invalidate_client_related_caches(str(sale.client_id))

    return sale


@router.delete("/{sale_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sale(
    sale_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("sales.write"))],
) -> None:
    sale = get_sale_or_404(db, sale_id)
    vehicle = db.get(Vehicle, sale.vehicle_id)

    old_data = {
        "vehicle_id": str(sale.vehicle_id),
        "client_id": str(sale.client_id),
        "sale_price": float(sale.sale_price),
    }

    if vehicle:
        vehicle.status = VehicleStatus.DISPONIBLE

    db.delete(sale)
    add_audit_log(
        db,
        action=AuditAction.DELETE,
        entity_type="sales",
        entity_id=sale_id,
        user_id=current_user.id,
        old_data=old_data,
    )
    db.commit()

    # Invalidate related caches after successful deletion
    await cache_service.invalidate_sale_related_caches()
    await cache_service.invalidate_vehicle_related_caches(str(sale.vehicle_id))
    await cache_service.invalidate_client_related_caches(str(sale.client_id))


@router.get("/{sale_id}", response_model=SaleResponse)
def get_sale(
    sale_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("sales.read"))],
) -> Sale:
    return get_sale_or_404(db, sale_id)


@router.get("/{sale_id}/pdf")
def get_sale_pdf(
    sale_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("sales.read"))],
):
    sale = get_sale_or_404(db, sale_id)

    vehicle = db.scalar(select(Vehicle).where(Vehicle.id == sale.vehicle_id))
    client = db.scalar(select(Client).where(Client.id == sale.client_id))
    branch = db.scalar(select(Branch).where(Branch.id == sale.branch_id))
    seller = db.scalar(select(User).where(User.id == sale.seller_user_id)) if sale.seller_user_id else None
    if not vehicle or not client or not branch:
        raise conflict("La venta tiene referencias incompletas")

    pdf_bytes = build_sale_pdf(
        company=get_company_info(db),
        sale=sale,
        vehicle=vehicle,
        client=client,
        branch=branch,
        seller=seller,
    )
    return stream_pdf(content=pdf_bytes, filename=f"venta_{sale.id}.pdf")
