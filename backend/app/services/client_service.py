from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.exceptions import not_found
from app.models.client import Client, ClientImage


CLIENT_LOAD_OPTIONS = (
    selectinload(Client.images),
    selectinload(Client.preference),
)


def get_client(db: Session, client_id: UUID) -> Client | None:
    return db.scalar(select(Client).options(*CLIENT_LOAD_OPTIONS).where(Client.id == client_id))


def get_client_or_404(db: Session, client_id: UUID) -> Client:
    client = get_client(db, client_id)
    if not client:
        raise not_found("Cliente no encontrado")
    return client


def get_client_image(db: Session, client_id: UUID, image_id: UUID) -> ClientImage | None:
    return db.scalar(
        select(ClientImage).where(ClientImage.id == image_id, ClientImage.client_id == client_id)
    )


def get_client_image_or_404(db: Session, client_id: UUID, image_id: UUID) -> ClientImage:
    image = get_client_image(db, client_id, image_id)
    if not image:
        raise not_found("Imagen no encontrada")
    return image


def unset_cover_images(db: Session, client_id: UUID) -> None:
    db.query(ClientImage).filter(ClientImage.client_id == client_id).update({"is_cover": False})


async def save_client_upload(*, client_id: UUID, file: UploadFile) -> str:
    if not file.filename:
        raise ValueError("Archivo inválido")

    suffix = Path(file.filename).suffix.lower() or ".bin"
    relative_dir = Path("clients") / str(client_id)
    absolute_dir = settings.media_path / relative_dir
    absolute_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4().hex}{suffix}"
    absolute_path = absolute_dir / filename
    content = await file.read()
    absolute_path.write_bytes(content)

    return f"{settings.MEDIA_URL}/{relative_dir.as_posix()}/{filename}"
