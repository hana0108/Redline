from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import not_found
from app.models.settings import SystemSettings
from app.services.pdf_generator import CompanyInfo

DEFAULT_BUSINESS_NAME = "Redline"


def get_settings(db: Session) -> SystemSettings | None:
    return db.scalar(select(SystemSettings).limit(1))


def get_settings_or_404(db: Session) -> SystemSettings:
    settings = get_settings(db)
    if not settings:
        raise not_found("Configuración no encontrada")
    return settings


def get_or_create_settings(db: Session) -> SystemSettings:
    settings = get_settings(db)
    if settings:
        return settings

    settings = SystemSettings(business_name=DEFAULT_BUSINESS_NAME)
    db.add(settings)
    db.flush()
    return settings


def get_company_info(db: Session) -> CompanyInfo:
    settings = get_settings(db)
    return CompanyInfo(
        business_name=settings.business_name if settings else DEFAULT_BUSINESS_NAME,
        contact_email=settings.contact_email if settings else None,
        contact_phone=settings.contact_phone if settings else None,
        whatsapp=settings.whatsapp if settings else None,
        address=settings.address if settings else None,
    )
