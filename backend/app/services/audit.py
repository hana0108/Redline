from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.enums import AuditAction
from app.services.serialization import json_safe



def add_audit_log(
    db: Session,
    *,
    action: AuditAction,
    entity_type: str,
    entity_id: UUID | None = None,
    user_id: UUID | None = None,
    old_data: dict | None = None,
    new_data: dict | None = None,
    ip_address: str | None = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_data=json_safe(old_data) if old_data else None,
            new_data=json_safe(new_data) if new_data else None,
            ip_address=ip_address,
            created_at=datetime.now(timezone.utc),
        )
    )
