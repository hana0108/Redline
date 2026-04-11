from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_permissions
from app.db.session import get_db
from app.models.client import Client, ClientPreference
from app.models.enums import AuditAction
from app.models.sale import Sale
from app.models.user import User
from app.schemas.client import ClientCreate, ClientHistoryResponse, ClientResponse, ClientUpdate, HistorySale
from app.services.audit import add_audit_log

router = APIRouter(prefix="/clients", tags=["clients"])


def _load_client(db: Session, client_id: UUID) -> Client | None:
    return db.scalar(
        select(Client)
        .options(selectinload(Client.preference))
        .where(Client.id == client_id)
    )


@router.get("", response_model=list[ClientResponse])
def list_clients(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("clients.read"))],
    search: str | None = Query(default=None),
) -> list[Client]:
    query = select(Client).options(selectinload(Client.preference)).order_by(Client.created_at.desc())
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
def create_client(
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
def update_client(
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
