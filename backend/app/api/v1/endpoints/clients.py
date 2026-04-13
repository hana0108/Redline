from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_permissions
from app.core.config import settings
from app.db.session import get_db
from app.models.client import Client, ClientImage, ClientPreference
from app.models.enums import AuditAction
from app.models.sale import Sale
from app.models.user import User
from app.schemas.client import (
    ClientImageResponse,
    ClientCreate,
    ClientHistoryResponse,
    ClientResponse,
    ClientUpdate,
    HistorySale,
)
from app.services.audit import add_audit_log
from app.services.cache_service import cache_service
from app.services.client_service import (
    get_client_image_or_404,
    get_client_or_404,
    save_client_upload,
    unset_cover_images,
)

router = APIRouter(prefix="/clients", tags=["clients"])


def _load_client(db: Session, client_id: UUID) -> Client | None:
    return db.scalar(
        select(Client)
        .options(selectinload(Client.preference), selectinload(Client.images))
        .where(Client.id == client_id)
    )


@router.get("", response_model=list[ClientResponse])
def list_clients(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("clients.read"))],
    search: str | None = Query(default=None),
) -> list[Client]:
    query = (
        select(Client)
        .options(selectinload(Client.preference), selectinload(Client.images))
        .order_by(Client.created_at.desc())
    )
    if search:
        like = f"%{search}%"
        query = query.where(
            or_(
                Client.full_name.ilike(like),
                Client.email.ilike(like),
                Client.phone.ilike(like),
                Client.document_number.ilike(like),
            )
        )
    return list(db.scalars(query).all())


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    payload: ClientCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("clients.write"))],
) -> Client:
    client_data = payload.model_dump(exclude={"preference"})
    client = Client(**client_data, created_by=current_user.id)
    db.add(client)
    db.flush()

    if payload.preference:
        preference = ClientPreference(client_id=client.id, **payload.preference.model_dump())
        db.add(preference)

    add_audit_log(
        db,
        action=AuditAction.CREATE,
        entity_type="clients",
        entity_id=client.id,
        user_id=current_user.id,
        new_data={"full_name": client.full_name, "email": client.email},
    )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Cliente duplicado o datos inválidos") from exc

    created = _load_client(db, client.id)

    # Invalidate related caches after successful creation
    await cache_service.invalidate_client_related_caches(str(client.id))

    return created


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(
    client_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("clients.read"))],
) -> Client:
    client = _load_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return client


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: UUID,
    payload: ClientUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("clients.write"))],
) -> Client:
    client = _load_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    update_data = payload.model_dump(exclude_unset=True, exclude={"preference"})
    old_data = {
        "full_name": client.full_name,
        "email": client.email,
        "phone": client.phone,
        "document_number": client.document_number,
    }

    for field, value in update_data.items():
        setattr(client, field, value)

    if "preference" in payload.model_fields_set:
        pref_data = payload.preference.model_dump() if payload.preference else None
        if pref_data:
            if client.preference:
                for field, value in pref_data.items():
                    setattr(client.preference, field, value)
            else:
                db.add(ClientPreference(client_id=client.id, **pref_data))
        elif client.preference:
            db.delete(client.preference)

    add_audit_log(
        db,
        action=AuditAction.UPDATE,
        entity_type="clients",
        entity_id=client.id,
        user_id=current_user.id,
        old_data=old_data,
        new_data=payload.model_dump(exclude_unset=True),
    )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Conflicto al actualizar cliente") from exc

    updated = _load_client(db, client.id)
    # Invalidate related caches after successful update
    await cache_service.invalidate_client_related_caches(str(client_id))
    return updated


@router.get("/{client_id}/history", response_model=ClientHistoryResponse)
def get_client_history(
    client_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("clients.read"))],
) -> ClientHistoryResponse:
    exists = db.scalar(select(Client.id).where(Client.id == client_id))
    if not exists:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    sales = [
        HistorySale(
            id=item.id,
            vehicle_id=item.vehicle_id,
            branch_id=item.branch_id,
            sale_date=item.sale_date,
            sale_price=float(item.sale_price),
            status=item.status.value,
        )
        for item in db.scalars(
            select(Sale).where(Sale.client_id == client_id).order_by(Sale.sale_date.desc())
        ).all()
    ]

    return ClientHistoryResponse(
        client_id=client_id,
        sales=sales,
    )


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    client_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("clients.write"))],
) -> None:
    client = _load_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    has_sales = db.scalar(select(Sale.id).where(Sale.client_id == client_id).limit(1))
    if has_sales:
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar el cliente porque tiene historial comercial asociado",
        )

    old_data = {
        "full_name": client.full_name,
        "email": client.email,
        "document_number": client.document_number,
    }
    db.delete(client)
    add_audit_log(
        db,
        action=AuditAction.DELETE,
        entity_type="clients",
        entity_id=client_id,
        user_id=current_user.id,
        old_data=old_data,
    )
    db.commit()


@router.get("/{client_id}/images", response_model=list[ClientImageResponse])
def list_client_images(
    client_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("clients.read"))],
) -> list[ClientImage]:
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    return sorted(
        db.scalars(select(ClientImage).where(ClientImage.client_id == client_id)).all(),
        key=lambda x: (not x.is_cover, x.sort_order),
    )


@router.post(
    "/{client_id}/images", response_model=ClientImageResponse, status_code=status.HTTP_201_CREATED
)
async def upload_client_image(
    client_id: UUID,
    file: Annotated[UploadFile, File()],
    sort_order: int = 0,
    is_cover: bool = False,
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(require_permissions("clients.write"))] = None,
) -> ClientImage:
    get_client_or_404(db, client_id)

    public_path = await save_client_upload(client_id=client_id, file=file)

    if is_cover:
        unset_cover_images(db, client_id)

    image = ClientImage(
        client_id=client_id, file_path=public_path, sort_order=sort_order, is_cover=is_cover
    )
    db.add(image)
    db.flush()

    add_audit_log(
        db,
        action=AuditAction.CREATE,
        entity_type="client_images",
        entity_id=image.id,
        user_id=current_user.id,
        new_data={"client_id": str(client_id), "file_path": public_path},
    )
    db.commit()
    return image


@router.patch("/{client_id}/images/{image_id}/cover", response_model=ClientImageResponse)
def set_cover_image(
    client_id: UUID,
    image_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("clients.write"))],
) -> ClientImage:
    image = get_client_image_or_404(db, client_id, image_id)

    unset_cover_images(db, client_id)
    image.is_cover = True
    db.commit()
    db.refresh(image)

    add_audit_log(
        db,
        action=AuditAction.UPDATE,
        entity_type="client_images",
        entity_id=image.id,
        user_id=current_user.id,
        new_data={"is_cover": True},
    )
    db.commit()
    return image


@router.patch("/{client_id}/images/{image_id}/sort", response_model=ClientImageResponse)
def update_client_image_sort(
    client_id: UUID,
    image_id: UUID,
    sort_order: int = 0,
    db: Annotated[Session, Depends(get_db)] = None,
    _: Annotated[User, Depends(require_permissions("clients.write"))] = None,
) -> ClientImage:
    image = get_client_image_or_404(db, client_id, image_id)
    image.sort_order = sort_order
    db.commit()
    db.refresh(image)
    return image


@router.delete("/{client_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client_image(
    client_id: UUID,
    image_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("clients.write"))],
) -> None:
    image = get_client_image_or_404(db, client_id, image_id)

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
        entity_type="client_images",
        entity_id=image_id,
        user_id=current_user.id,
        old_data={"file_path": old_path},
    )
    db.commit()
