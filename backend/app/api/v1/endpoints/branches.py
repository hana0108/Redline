from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.core.exceptions import not_found
from app.db.session import get_db
from app.models.branch import Branch
from app.models.enums import AuditAction
from app.models.user import User
from app.schemas.branch import BranchCreate, BranchResponse, BranchUpdate
from app.services.audit import add_audit_log

router = APIRouter(prefix="/branches", tags=["branches"])


@router.get("", response_model=list[BranchResponse])
def list_branches(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("branches.read"))],
) -> list[Branch]:
    return list(db.scalars(select(Branch).order_by(Branch.name.asc())).all())


@router.post("", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
def create_branch(
    payload: BranchCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("branches.write"))],
) -> Branch:
    branch = Branch(**payload.model_dump())
    db.add(branch)
    db.flush()

    add_audit_log(
        db,
        action=AuditAction.CREATE,
        entity_type="branches",
        entity_id=branch.id,
        user_id=current_user.id,
        new_data={
            "name": branch.name,
            "address": branch.address,
            "phone": branch.phone,
            "email": branch.email,
            "status": branch.status.value if hasattr(branch.status, "value") else str(branch.status),
        },
    )

    db.commit()
    db.refresh(branch)
    return branch


@router.get("/{branch_id}", response_model=BranchResponse)
def get_branch(
    branch_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("branches.read"))],
) -> Branch:
    branch = db.get(Branch, branch_id)
    if not branch:
        raise not_found("Sucursal no encontrada")
    return branch


@router.patch("/{branch_id}", response_model=BranchResponse)
def update_branch(
    branch_id: UUID,
    payload: BranchUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("branches.write"))],
) -> Branch:
    branch = db.get(Branch, branch_id)
    if not branch:
        raise not_found("Sucursal no encontrada")

    old_data = {
        "name": branch.name,
        "address": branch.address,
        "phone": branch.phone,
        "email": branch.email,
        "status": branch.status.value if hasattr(branch.status, "value") else str(branch.status),
    }

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(branch, field, value)

    add_audit_log(
        db,
        action=AuditAction.UPDATE,
        entity_type="branches",
        entity_id=branch.id,
        user_id=current_user.id,
        old_data=old_data,
        new_data=update_data,
    )

    db.commit()
    db.refresh(branch)
    return branch
