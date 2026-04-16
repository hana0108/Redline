from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.core.config import settings
from app.db.session import get_db
from app.models.document import Document
from app.models.enums import AuditAction
from app.models.user import User
from app.schemas.document import (
    DocumentCreate,
    DocumentResponse,
    DocumentUpdate,
    DocumentListResponse,
)
from app.services.audit import add_audit_log
from app.services.document_service import (
    get_document_or_404,
    get_documents_by_entity,
    save_document_upload,
    validate_entity_exists,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
def list_documents(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("documents.read"))],
    entity_type: str | None = Query(None),
    entity_id: UUID | None = Query(None),
    document_type: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> DocumentListResponse:
    query = select(Document)

    if entity_type:
        query = query.where(Document.entity_type == entity_type)
    if entity_id:
        query = query.where(Document.entity_id == entity_id)
    if document_type:
        query = query.where(Document.document_type == document_type)

    query = query.order_by(Document.created_at.desc()).offset(skip).limit(limit)

    documents = list(db.scalars(query).all())
    count_query = select(func.count(Document.id))
    if entity_type:
        count_query = count_query.where(Document.entity_type == entity_type)
    if entity_id:
        count_query = count_query.where(Document.entity_id == entity_id)
    if document_type:
        count_query = count_query.where(Document.document_type == document_type)
    total = db.scalar(count_query) or 0

    return DocumentListResponse(documents=documents, total=total or 0)


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: Annotated[UploadFile, File()],
    entity_type: str,
    entity_id: UUID,
    document_type: str,
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(require_permissions("documents.write"))] = None,
) -> DocumentResponse:
    # Validar que la entidad existe
    validate_entity_exists(db, entity_type, entity_id)

    # Guardar archivo
    public_path = await save_document_upload(
        entity_type=entity_type, entity_id=entity_id, document_type=document_type, file=file
    )

    # Crear registro en BD
    document = Document(
        entity_type=entity_type,
        entity_id=entity_id,
        file_path=public_path,
        document_type=document_type,
    )
    db.add(document)
    db.flush()

    add_audit_log(
        db,
        action=AuditAction.CREATE,
        entity_type="documents",
        entity_id=document.id,
        user_id=current_user.id,
        new_data={
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "document_type": document_type,
            "file_path": public_path,
        },
    )
    db.commit()
    return get_document_or_404(db, document.id)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("documents.read"))],
) -> DocumentResponse:
    return get_document_or_404(db, document_id)


@router.get("/{document_id}/download")
def download_document(
    document_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("documents.read"))],
):
    document = get_document_or_404(db, document_id)

    # Convertir path público a path local
    if document.file_path.startswith(settings.MEDIA_URL):
        relative = document.file_path.removeprefix(settings.MEDIA_URL).lstrip("/")
        local_path = settings.media_path / Path(relative)

        if not local_path.exists():
            raise HTTPException(status_code=404, detail="Archivo no encontrado en disco")

        return {
            "url": document.file_path,
            "filename": local_path.name,
            "content_type": "application/octet-stream",  # Generic, could be improved
        }

    raise HTTPException(status_code=404, detail="Archivo no accesible")


@router.patch("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: UUID,
    payload: DocumentUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("documents.write"))],
) -> DocumentResponse:
    document = get_document_or_404(db, document_id)

    old_data = {"document_type": document.document_type.value}
    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(document, field, value)

    add_audit_log(
        db,
        action=AuditAction.UPDATE,
        entity_type="documents",
        entity_id=document_id,
        user_id=current_user.id,
        old_data=old_data,
        new_data=update_data,
    )

    db.commit()
    db.refresh(document)
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("documents.write"))],
) -> None:
    document = get_document_or_404(db, document_id)

    old_path = document.file_path
    # Eliminar archivo físico
    if old_path.startswith(settings.MEDIA_URL):
        relative = old_path.removeprefix(settings.MEDIA_URL).lstrip("/")
        local_path = settings.media_path / Path(relative)
        if local_path.exists():
            local_path.unlink()

    add_audit_log(
        db,
        action=AuditAction.DELETE,
        entity_type="documents",
        entity_id=document_id,
        user_id=current_user.id,
        old_data={"file_path": old_path, "entity_type": document.entity_type},
    )

    db.delete(document)
    db.commit()


# Endpoints específicos por entidad
@router.get("/entity/{entity_type}/{entity_id}", response_model=list[DocumentResponse])
def get_documents_by_entity_endpoint(
    entity_type: str,
    entity_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("documents.read"))],
) -> list[DocumentResponse]:
    # Validar que la entidad existe
    validate_entity_exists(db, entity_type, entity_id)
    return get_documents_by_entity(db, entity_type, entity_id)
