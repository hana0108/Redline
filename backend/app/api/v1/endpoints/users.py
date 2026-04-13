from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_permissions
from app.core.security import get_password_hash
from app.db.session import get_db
from app.models.enums import AuditAction
from app.models.role import Role
from app.models.user import User, UserBranchAccess
from app.models.branch import Branch
from app.models.sale import Sale
from app.schemas.user import (
    UserBranchesUpdate,
    UserCreate,
    UserResponse,
    UserStatusUpdate,
    UserUpdate,
)
from app.services.audit import add_audit_log

router = APIRouter(prefix="/users", tags=["users"])


def _load_user(db: Session, user_id: UUID) -> User | None:
    return db.scalar(
        select(User)
        .options(selectinload(User.role), selectinload(User.branch_links))
        .where(User.id == user_id)
    )


def _to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        role=user.role,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        status=user.status,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
        branch_ids=[link.branch_id for link in user.branch_links],
    )


def _validate_role_and_branches(db: Session, role_id: UUID, branch_ids: list[UUID]) -> None:
    role_exists = db.scalar(select(Role.id).where(Role.id == role_id))
    if not role_exists:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    if branch_ids:
        found = set(db.scalars(select(Branch.id).where(Branch.id.in_(branch_ids))).all())
        missing = [str(branch_id) for branch_id in branch_ids if branch_id not in found]
        if missing:
            raise HTTPException(
                status_code=404,
                detail=f"Sucursales no encontradas: {', '.join(missing)}",
            )


@router.get("", response_model=list[UserResponse])
def list_users(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("users.read"))],
) -> list[UserResponse]:
    users = list(
        db.scalars(
            select(User)
            .options(selectinload(User.role), selectinload(User.branch_links))
            .order_by(User.full_name)
        ).all()
    )
    return [_to_response(user) for user in users]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("users.write"))],
) -> UserResponse:
    _validate_role_and_branches(db, payload.role_id, payload.branch_ids)

    user = User(
        role_id=payload.role_id,
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        password_hash=get_password_hash(payload.password),
        status=payload.status,
    )
    db.add(user)
    db.flush()

    for branch_id in payload.branch_ids:
        db.add(UserBranchAccess(user_id=user.id, branch_id=branch_id))

    add_audit_log(
        db,
        action=AuditAction.CREATE,
        entity_type="users",
        entity_id=user.id,
        user_id=current_user.id,
        new_data={
            "email": user.email,
            "role_id": str(user.role_id),
            "branch_ids": [str(branch_id) for branch_id in payload.branch_ids],
        },
    )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email duplicado o datos inválidos") from exc

    created = _load_user(db, user.id)
    return _to_response(created)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("users.read"))],
) -> UserResponse:
    user = _load_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return _to_response(user)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    payload: UserUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("users.write"))],
) -> UserResponse:
    user = _load_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    update_data = payload.model_dump(exclude_unset=True)

    if "role_id" in update_data:
        _validate_role_and_branches(db, update_data["role_id"], [])

    old_data = {
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "role_id": str(user.role_id),
        "status": user.status.value,
    }

    password = update_data.pop("password", None)
    for field, value in update_data.items():
        setattr(user, field, value)

    if password:
        user.password_hash = get_password_hash(password)

    add_audit_log(
        db,
        action=AuditAction.UPDATE,
        entity_type="users",
        entity_id=user.id,
        user_id=current_user.id,
        old_data=old_data,
        new_data={
            **update_data,
            **({"password": "updated"} if password else {}),
        },
    )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Conflicto al actualizar usuario") from exc

    updated = _load_user(db, user.id)
    return _to_response(updated)


@router.patch("/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: UUID,
    payload: UserStatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("users.write"))],
) -> UserResponse:
    user = _load_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    old_status = user.status.value
    user.status = payload.status

    add_audit_log(
        db,
        action=AuditAction.STATUS_CHANGE,
        entity_type="users",
        entity_id=user.id,
        user_id=current_user.id,
        old_data={"status": old_status},
        new_data={"status": payload.status.value},
    )

    db.commit()
    updated = _load_user(db, user.id)
    return _to_response(updated)


@router.put("/{user_id}/branches", response_model=UserResponse)
def replace_user_branches(
    user_id: UUID,
    payload: UserBranchesUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("users.write"))],
) -> UserResponse:
    user = _load_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    _validate_role_and_branches(db, user.role_id, payload.branch_ids)
    old_branch_ids = [str(link.branch_id) for link in user.branch_links]

    db.query(UserBranchAccess).filter(UserBranchAccess.user_id == user.id).delete()
    for branch_id in payload.branch_ids:
        db.add(UserBranchAccess(user_id=user.id, branch_id=branch_id))

    add_audit_log(
        db,
        action=AuditAction.UPDATE,
        entity_type="users",
        entity_id=user.id,
        user_id=current_user.id,
        old_data={"branch_ids": old_branch_ids},
        new_data={"branch_ids": [str(branch_id) for branch_id in payload.branch_ids]},
    )

    db.commit()
    updated = _load_user(db, user.id)
    return _to_response(updated)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("users.write"))],
) -> None:
    user = _load_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # No permitir auto-eliminarse
    if user.id == current_user.id:
        raise HTTPException(status_code=403, detail="No puedes eliminar tu propio usuario")

    # No permitir eliminar admin principal
    if user.role.code == "admin" and user.id == db.scalar(
        select(User.id).join(Role).where(Role.code == "admin").limit(1)
    ):
        raise HTTPException(
            status_code=403,
            detail="No se puede eliminar el administrador principal"
        )

    # Validar que no haya ventas registradas por este usuario
    sale_count = db.scalar(select(func.count(Sale.id)).where(Sale.seller_id == user_id))
    if sale_count:
        raise HTTPException(
            status_code=409,
            detail=f"No se puede eliminar el usuario: tiene {sale_count} venta(s) registrada(s)"
        )

    add_audit_log(
        db,
        action=AuditAction.DELETE,
        entity_type="users",
        entity_id=user_id,
        user_id=current_user.id,
        old_data={"email": user.email, "full_name": user.full_name},
    )

    # Eliminar acceso a sucursales
    db.query(UserBranchAccess).filter(UserBranchAccess.user_id == user_id).delete()

    # Eliminar usuario
    db.delete(user)
    db.commit()
