from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.security import get_subject_from_token
from app.db.session import get_db
from app.models.enums import StatusGeneric
from app.models.role import Role, RolePermission
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")


def _permission_codes(user: User) -> set[str]:
    if not user.role:
        return set()
    return {
        link.permission.code
        for link in user.role.permissions
        if link.permission and link.permission.code
    }


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    try:
        user_id = UUID(get_subject_from_token(token))
    except (ValueError, JWTError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido") from exc

    query = (
        select(User)
        .options(
            selectinload(User.role).selectinload(Role.permissions).selectinload(RolePermission.permission),
            selectinload(User.branch_links),
        )
        .where(User.id == user_id)
    )
    user = db.scalar(query)
    if not user or user.status != StatusGeneric.ACTIVE:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no válido o inactivo")
    return user


def require_roles(*allowed_roles: str) -> Callable[[User], User]:
    allowed = {role.lower() for role in allowed_roles}

    def dependency(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        role_name = current_user.role.name.lower() if current_user.role else ""
        if role_name not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para realizar esta acción")
        return current_user

    return dependency


def require_permissions(*permission_codes: str) -> Callable[[User], User]:
    required = set(permission_codes)

    def dependency(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        user_codes = _permission_codes(current_user)
        if not required.issubset(user_codes):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos suficientes")
        return current_user

    return dependency
