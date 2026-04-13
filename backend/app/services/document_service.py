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


async def save_document_upload(
    *, entity_type: str, entity_id: UUID, document_type: str, file: UploadFile
) -> str:
    if not file.filename:
        raise ValueError("Archivo inválido")

    # Validar tipos de archivo permitidos
    allowed_extensions = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.jpg', '.jpeg', '.png'}
    suffix = Path(file.filename).suffix.lower()
    if suffix not in allowed_extensions:
        raise ValueError(f"Tipo de archivo no permitido: {suffix}")

    # Crear directorio por entidad
    relative_dir = Path("documents") / entity_type / str(entity_id)
    absolute_dir = settings.media_path / relative_dir
    absolute_dir.mkdir(parents=True, exist_ok=True)

    # Generar nombre único
    filename = f"{uuid4().hex}_{file.filename}"
    absolute_path = absolute_dir / filename
    content = await file.read()
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