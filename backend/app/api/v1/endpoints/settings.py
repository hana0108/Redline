from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.db.session import get_db
from app.models.enums import AuditAction
from app.models.user import User
from app.schemas.settings import SystemSettingsResponse, SystemSettingsUpdate
from app.services.audit import add_audit_log
from app.services.settings_service import get_or_create_settings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SystemSettingsResponse)
def get_settings(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("settings.read"))],
):
    return get_or_create_settings(db)


@router.patch("", response_model=SystemSettingsResponse)
def update_settings(
    payload: SystemSettingsUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("settings.write"))],
):
    settings = get_or_create_settings(db)

    update_data = payload.model_dump(exclude_unset=True)
    old_data = {field: getattr(settings, field) for field in update_data.keys()}
    for field, value in update_data.items():
        setattr(settings, field, value)

    add_audit_log(
        db,
        action=AuditAction.UPDATE,
        entity_type="system_settings",
        entity_id=settings.id,
        user_id=current_user.id,
        old_data=old_data,
        new_data=update_data,
    )
    db.commit()
    db.refresh(settings)
    return settings
