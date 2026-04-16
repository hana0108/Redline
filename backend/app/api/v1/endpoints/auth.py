from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.enums import AuditAction, StatusGeneric
from app.models.role import Role, RolePermission
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserSummary
from app.services.audit import add_audit_log

router = APIRouter(prefix="/auth", tags=["auth"])


def authenticate_user(*, email: str, password: str, request: Request, db: Session) -> TokenResponse:
    user = db.scalar(
        select(User)
        .options(
            selectinload(User.role)
            .selectinload(Role.permissions)
            .selectinload(RolePermission.permission)
        )
        .where(User.email == email)
    )
    if not user or not verify_password(password, user.password_hash):
        add_audit_log(
            db,
            user_id=user.id if user else None,
            action=AuditAction.LOGIN_FAILED,
            entity_type="users",
            entity_id=user.id if user else None,
            new_data={"email": email, "reason": "invalid_credentials"},
            ip_address=request.client.host if request.client else None,
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas"
        )
    if user.status != StatusGeneric.ACTIVE:
        add_audit_log(
            db,
            user_id=user.id,
            action=AuditAction.LOGIN_FAILED,
            entity_type="users",
            entity_id=user.id,
            new_data={"email": email, "reason": "inactive_user"},
            ip_address=request.client.host if request.client else None,
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")

    user.last_login_at = datetime.now(timezone.utc)
    add_audit_log(
        db,
        user_id=user.id,
        action=AuditAction.LOGIN,
        entity_type="users",
        entity_id=user.id,
        new_data={"email": user.email},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token, token_type="bearer")


@router.post("/login", response_model=TokenResponse)
def login_json(
    payload: Annotated[LoginRequest, Body(...)],
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    return authenticate_user(email=payload.email, password=payload.password, request=request, db=db)


@router.post("/token", response_model=TokenResponse)
def login_oauth2(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    return authenticate_user(
        email=form_data.username, password=form_data.password, request=request, db=db
    )


@router.get("/me", response_model=UserSummary)
def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserSummary:
    role_name = current_user.role.name if current_user.role else ""
    permissions = []
    if current_user.role:
        permissions = [
            link.permission.code
            for link in current_user.role.permissions
            if link.permission and link.permission.code
        ]

    return UserSummary(
        id=str(current_user.id),
        full_name=current_user.full_name,
        email=current_user.email,
        role=role_name,
        permissions=permissions,
        branch_ids=[str(link.branch_id) for link in current_user.branch_links],
    )
