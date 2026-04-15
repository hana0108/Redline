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


_ALLOWED_CLIENT_IMAGE_SIGNATURES: dict[bytes, str] = {
    b"\xff\xd8\xff": ".jpg",
    b"\x89PNG": ".png",
    b"GIF8": ".gif",
    b"RIFF": ".webp",  # RIFF....WEBP — checked below
}
_MAX_CLIENT_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


async def save_client_upload(*, client_id: UUID, file: UploadFile) -> str:
    if not file.filename:
        raise ValueError("Archivo inválido")

    content = await file.read()

    if len(content) > _MAX_CLIENT_UPLOAD_BYTES:
        raise ValueError("El archivo supera el tamaño máximo permitido de 10 MB")

    detected_suffix: str | None = None
    for magic, ext in _ALLOWED_CLIENT_IMAGE_SIGNATURES.items():
        if content[: len(magic)].startswith(magic):
            if ext == ".webp" and content[8:12] != b"WEBP":
                continue
            detected_suffix = ext
            break
    if detected_suffix is None:
        raise ValueError(
            "Tipo de archivo no permitido. Solo se aceptan imágenes JPEG, PNG, GIF o WebP"
        )

    relative_dir = Path("clients") / str(client_id)
    absolute_dir = settings.media_path / relative_dir
    absolute_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4().hex}{detected_suffix}"
    absolute_path = absolute_dir / filename
    absolute_path.write_bytes(content)

    return f"{settings.MEDIA_URL}/{relative_dir.as_posix()}/{filename}"
