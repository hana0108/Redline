from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.core.config import settings
from app.db.session import get_db
from app.models.enums import AuditAction
from app.models.sale import Sale
from app.models.user import User
from app.models.vehicle import Vehicle, VehicleImage, VehicleStatusHistory
from app.schemas.vehicle import (
    VehicleCreate,
    VehicleImageCreate,
    VehicleImageResponse,
    VehicleImageSortUpdate,
    VehicleResponse,
    VehicleStatusUpdate,
    VehicleUpdate,
)
from app.services.audit import add_audit_log
from app.services.vehicle_service import (
    ensure_branch_exists,
    get_vehicle_image_or_404,
    get_vehicle_or_404,
    save_vehicle_upload,
    unset_cover_images,
)

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("", response_model=list[VehicleResponse])
def list_vehicles(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("vehicles.read"))],
    status_filter: str | None = Query(default=None, alias="status"),
    branch_id: UUID | None = None,
    search: str | None = None,
) -> list[Vehicle]:
    query = select(Vehicle)
    if status_filter:
        query = query.where(Vehicle.status == status_filter)
    if branch_id:
        query = query.where(Vehicle.branch_id == branch_id)
    if search:
        like = f"%{search}%"
        query = query.where(
            Vehicle.brand.ilike(like)
            | Vehicle.model.ilike(like)
            | Vehicle.vin.ilike(like)
            | Vehicle.plate.ilike(like)
        )
    query = query.order_by(Vehicle.created_at.desc())
    return list(db.scalars(query).all())


@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    payload: VehicleCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("vehicles.write"))],
) -> Vehicle:
    ensure_branch_exists(db, payload.branch_id)
    vehicle = Vehicle(**payload.model_dump(), created_by=current_user.id)
    db.add(vehicle)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="VIN o datos únicos duplicados") from exc

    db.refresh(vehicle)
    add_audit_log(
        db,
        action=AuditAction.CREATE,
        entity_type="vehicles",
        entity_id=vehicle.id,
        user_id=current_user.id,
        new_data={"vin": vehicle.vin, "brand": vehicle.brand, "model": vehicle.model},
    )
    db.commit()
    return get_vehicle_or_404(db, vehicle.id)


@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(
    vehicle_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("vehicles.read"))],
) -> Vehicle:
    return get_vehicle_or_404(db, vehicle_id)


@router.patch("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(
    vehicle_id: UUID,
    payload: VehicleUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("vehicles.write"))],
) -> Vehicle:
    vehicle = get_vehicle_or_404(db, vehicle_id)

    update_data = payload.model_dump(exclude_unset=True)
    if "branch_id" in update_data:
        ensure_branch_exists(db, update_data["branch_id"])

    old_data = {
        "branch_id": str(vehicle.branch_id),
        "price": float(vehicle.price),
        "mileage": vehicle.mileage,
        "description": vehicle.description,
    }
    for field, value in update_data.items():
        setattr(vehicle, field, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Conflicto de datos al actualizar") from exc

    add_audit_log(
        db,
        action=AuditAction.UPDATE,
        entity_type="vehicles",
        entity_id=vehicle.id,
        user_id=current_user.id,
        old_data=old_data,
        new_data=update_data,
    )
    db.commit()
    return get_vehicle_or_404(db, vehicle.id)


@router.patch("/{vehicle_id}/status", response_model=VehicleResponse)
def update_vehicle_status(
    vehicle_id: UUID,
    payload: VehicleStatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("vehicles.write"))],
) -> Vehicle:
    vehicle = get_vehicle_or_404(db, vehicle_id)

    old_status = vehicle.status
    vehicle.status = payload.status
    db.add(
        VehicleStatusHistory(
            vehicle_id=vehicle.id,
            old_status=old_status,
            new_status=payload.status,
            changed_by=current_user.id,
            notes=payload.notes,
        )
    )
    add_audit_log(
        db,
        action=AuditAction.STATUS_CHANGE,
        entity_type="vehicles",
        entity_id=vehicle.id,
        user_id=current_user.id,
        old_data={"status": old_status.value},
        new_data={"status": payload.status.value, "notes": payload.notes},
    )

    db.commit()
    return get_vehicle_or_404(db, vehicle.id)


@router.get("/{vehicle_id}/images", response_model=list[VehicleImageResponse])
def list_vehicle_images(
    vehicle_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("vehicles.read"))],
) -> list[VehicleImage]:
    get_vehicle_or_404(db, vehicle_id)
    return list(
        db.scalars(
            select(VehicleImage)
            .where(VehicleImage.vehicle_id == vehicle_id)
            .order_by(VehicleImage.is_cover.desc(), VehicleImage.sort_order.asc())
        ).all()
    )


@router.post("/{vehicle_id}/images", response_model=VehicleImageResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle_image_from_path(
    vehicle_id: UUID,
    payload: VehicleImageCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("vehicles.write"))],
) -> VehicleImage:
    get_vehicle_or_404(db, vehicle_id)

    if payload.is_cover:
        unset_cover_images(db, vehicle_id)

    image = VehicleImage(vehicle_id=vehicle_id, **payload.model_dump())
    db.add(image)
    db.commit()
    db.refresh(image)

    add_audit_log(
        db,
        action=AuditAction.CREATE,
        entity_type="vehicle_images",
        entity_id=image.id,
        user_id=current_user.id,
        new_data={"vehicle_id": str(vehicle_id), "file_path": image.file_path},
    )
    db.commit()
    return image


@router.post("/{vehicle_id}/images/upload", response_model=VehicleImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_vehicle_image(
    vehicle_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("vehicles.write"))],
    file: UploadFile = File(...),
    sort_order: int = Form(0),
    is_cover: bool = Form(False),
) -> VehicleImage:
    get_vehicle_or_404(db, vehicle_id)
    try:
        public_path = await save_vehicle_upload(vehicle_id=vehicle_id, file=file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if is_cover:
        unset_cover_images(db, vehicle_id)

    image = VehicleImage(
        vehicle_id=vehicle_id,
        file_path=public_path,
        sort_order=sort_order,
        is_cover=is_cover,
    )
    db.add(image)
    db.commit()
    db.refresh(image)

    add_audit_log(
        db,
        action=AuditAction.CREATE,
        entity_type="vehicle_images",
        entity_id=image.id,
        user_id=current_user.id,
        new_data={"vehicle_id": str(vehicle_id), "file_path": public_path},
    )
    db.commit()
    return image


@router.patch("/{vehicle_id}/images/{image_id}/cover", response_model=VehicleImageResponse)
def set_cover_image(
    vehicle_id: UUID,
    image_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("vehicles.write"))],
) -> VehicleImage:
    image = get_vehicle_image_or_404(db, vehicle_id, image_id)

    unset_cover_images(db, vehicle_id)
    image.is_cover = True
    db.commit()
    db.refresh(image)

    add_audit_log(
        db,
        action=AuditAction.UPDATE,
        entity_type="vehicle_images",
        entity_id=image.id,
        user_id=current_user.id,
        new_data={"is_cover": True},
    )
    db.commit()
    return image


@router.patch("/{vehicle_id}/images/{image_id}/sort", response_model=VehicleImageResponse)
def update_vehicle_image_sort(
    vehicle_id: UUID,
    image_id: UUID,
    payload: VehicleImageSortUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("vehicles.write"))],
) -> VehicleImage:
    image = get_vehicle_image_or_404(db, vehicle_id, image_id)
    image.sort_order = payload.sort_order
    db.commit()
    db.refresh(image)
    return image


@router.delete("/{vehicle_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle_image(
    vehicle_id: UUID,
    image_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("vehicles.write"))],
) -> None:
    image = get_vehicle_image_or_404(db, vehicle_id, image_id)

    old_path = image.file_path
    if old_path.startswith(settings.MEDIA_URL):
        relative = old_path.removeprefix(settings.MEDIA_URL).lstrip("/")
        local_path = settings.media_path / Path(relative)
        if local_path.exists():
            local_path.unlink()

    db.delete(image)
    db.commit()

    add_audit_log(
        db,
        action=AuditAction.DELETE,
        entity_type="vehicle_images",
        entity_id=image_id,
        user_id=current_user.id,
        old_data={"file_path": old_path},
    )
    db.commit()


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(
    vehicle_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("vehicles.write"))],
) -> None:
    vehicle = get_vehicle_or_404(db, vehicle_id)

    has_sales = db.scalar(select(Sale.id).where(Sale.vehicle_id == vehicle_id).limit(1))
    if has_sales:
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar el vehículo porque tiene historial comercial asociado",
        )

    old_data = {
        "vin": vehicle.vin,
        "brand": vehicle.brand,
        "model": vehicle.model,
        "status": vehicle.status.value,
    }
    db.delete(vehicle)
    add_audit_log(
        db,
        action=AuditAction.DELETE,
        entity_type="vehicles",
        entity_id=vehicle_id,
        user_id=current_user.id,
        old_data=old_data,
    )
    db.commit()
