from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import not_found
from app.models.document import Document


def get_document(db: Session, document_id: UUID) -> Document | None:
    return db.scalar(select(Document).where(Document.id == document_id))


def get_document_or_404(db: Session, document_id: UUID) -> Document:
    document = get_document(db, document_id)
    if not document:
        raise not_found("Documento no encontrado")
    return document


def get_documents_by_entity(db: Session, entity_type: str, entity_id: UUID) -> list[Document]:
    return list(
        db.scalars(
            select(Document)
            .where(Document.entity_type == entity_type, Document.entity_id == entity_id)
            .order_by(Document.created_at.desc())
        ).all()
    )


_MAX_DOCUMENT_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB

# Magic-byte signatures → safe extension
_DOCUMENT_SIGNATURES: list[tuple[bytes, str]] = [
    (b"%PDF", ".pdf"),
    (b"\xff\xd8\xff", ".jpg"),
    (b"\x89PNG", ".png"),
    (b"PK\x03\x04", ".office"),  # docx / xlsx (ZIP-based Office)
    (b"\xd0\xcf\x11\xe0", ".office"),  # doc / xls (OLE Compound)
]


async def save_document_upload(
    *, entity_type: str, entity_id: UUID, document_type: str, file: UploadFile
) -> str:
    if not file.filename:
        raise ValueError("Archivo inválido")

    content = await file.read()

    if len(content) > _MAX_DOCUMENT_UPLOAD_BYTES:
        raise ValueError("El archivo supera el tamaño máximo permitido de 50 MB")

    original_suffix = Path(file.filename).suffix.lower()
    detected_suffix: str | None = None
    for magic, ext in _DOCUMENT_SIGNATURES:
        if content[: len(magic)].startswith(magic):
            detected_suffix = ext
            break

    if detected_suffix == ".office":
        if original_suffix not in {".doc", ".docx", ".xls", ".xlsx"}:
            raise ValueError("Tipo de archivo no permitido")
        detected_suffix = original_suffix
    elif detected_suffix is None:
        # Permit plain-text only when extension is .txt and content is valid UTF-8
        if original_suffix == ".txt":
            try:
                content.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ValueError("El archivo .txt no está codificado en UTF-8") from exc
            detected_suffix = ".txt"
        else:
            raise ValueError(
                "Tipo de archivo no permitido. Se aceptan: PDF, imágenes, documentos Office o texto plano"
            )

    # Crear directorio por entidad
    relative_dir = Path("documents") / entity_type / str(entity_id)
    absolute_dir = settings.media_path / relative_dir
    absolute_dir.mkdir(parents=True, exist_ok=True)

    # Nombre único — no usar el nombre original para evitar path traversal
    filename = f"{uuid4().hex}{detected_suffix}"
    absolute_path = absolute_dir / filename
    absolute_path.write_bytes(content)

    return f"{settings.MEDIA_URL}/{relative_dir.as_posix()}/{filename}"


def validate_entity_exists(db: Session, entity_type: str, entity_id: UUID) -> None:
    """Valida que la entidad referenciada existe"""
    if entity_type == "vehicles":
        from app.models.vehicle import Vehicle

        if not db.scalar(select(Vehicle.id).where(Vehicle.id == entity_id)):
            raise not_found("Vehículo no encontrado")
    elif entity_type == "clients":
        from app.models.client import Client

        if not db.scalar(select(Client.id).where(Client.id == entity_id)):
            raise not_found("Cliente no encontrado")
    elif entity_type == "sales":
        from app.models.sale import Sale

        if not db.scalar(select(Sale.id).where(Sale.id == entity_id)):
            raise not_found("Venta no encontrada")
    elif entity_type == "branches":
        from app.models.branch import Branch

        if not db.scalar(select(Branch.id).where(Branch.id == entity_id)):
            raise not_found("Sucursal no encontrada")
    # Agregar más entidades según sea necesario
