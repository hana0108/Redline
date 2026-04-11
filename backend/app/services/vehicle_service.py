from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.exceptions import not_found
from app.models.branch import Branch
from app.models.vehicle import Vehicle, VehicleImage


VEHICLE_LOAD_OPTIONS = (
    selectinload(Vehicle.images),
    selectinload(Vehicle.branch),
)


def get_vehicle(db: Session, vehicle_id: UUID) -> Vehicle | None:
    return db.scalar(select(Vehicle).options(*VEHICLE_LOAD_OPTIONS).where(Vehicle.id == vehicle_id))


def get_vehicle_or_404(db: Session, vehicle_id: UUID) -> Vehicle:
    vehicle = get_vehicle(db, vehicle_id)
    if not vehicle:
        raise not_found("Vehículo no encontrado")
    return vehicle


def ensure_branch_exists(db: Session, branch_id: UUID) -> None:
    if not db.scalar(select(Branch.id).where(Branch.id == branch_id)):
        raise not_found("Sucursal no encontrada")


def get_vehicle_image(db: Session, vehicle_id: UUID, image_id: UUID) -> VehicleImage | None:
    return db.scalar(
        select(VehicleImage).where(VehicleImage.id == image_id, VehicleImage.vehicle_id == vehicle_id)
    )


def get_vehicle_image_or_404(db: Session, vehicle_id: UUID, image_id: UUID) -> VehicleImage:
    image = get_vehicle_image(db, vehicle_id, image_id)
    if not image:
        raise not_found("Imagen no encontrada")
    return image


def unset_cover_images(db: Session, vehicle_id: UUID) -> None:
    db.query(VehicleImage).filter(VehicleImage.vehicle_id == vehicle_id).update({"is_cover": False})


async def save_vehicle_upload(*, vehicle_id: UUID, file: UploadFile) -> str:
    if not file.filename:
        raise ValueError("Archivo inválido")

    suffix = Path(file.filename).suffix.lower() or ".bin"
    relative_dir = Path("vehicles") / str(vehicle_id)
    absolute_dir = settings.media_path / relative_dir
    absolute_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4().hex}{suffix}"
    absolute_path = absolute_dir / filename
    content = await file.read()
    absolute_path.write_bytes(content)

    return f"{settings.MEDIA_URL}/{relative_dir.as_posix()}/{filename}"
