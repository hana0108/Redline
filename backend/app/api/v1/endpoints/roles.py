from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_permissions
from app.db.session import get_db
from app.models.role import Permission, Role, RolePermission
from app.models.user import User
from app.schemas.role import PermissionResponse, RoleResponse

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=list[RoleResponse])
def list_roles(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("roles.read"))],
) -> list[RoleResponse]:
    roles = list(
        db.scalars(
            select(Role)
            .options(
                selectinload(Role.permissions).selectinload(RolePermission.permission)
            )
            .order_by(Role.name)
        ).all()
    )
    return [
        RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            created_at=role.created_at,
            permission_codes=[
                link.permission.code
                for link in role.permissions
                if link.permission and link.permission.code
            ],
        )
        for role in roles
    ]


@router.get("/permissions", response_model=list[PermissionResponse])
def list_permissions(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("roles.read"))],
) -> list[Permission]:
    return list(db.scalars(select(Permission).order_by(Permission.code)).all())
