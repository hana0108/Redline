from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SystemSettingsBase(BaseModel):
    business_name: str = Field(min_length=2, max_length=180)
    logo_path: str | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=30)
    whatsapp: str | None = Field(default=None, max_length=30)
    address: str | None = None
    facebook: str | None = Field(default=None, max_length=255)
    instagram: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=255)
    terms_and_conditions: str | None = None
    privacy_policy: str | None = None


class SystemSettingsUpdate(BaseModel):
    business_name: str | None = Field(default=None, min_length=2, max_length=180)
    logo_path: str | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=30)
    whatsapp: str | None = Field(default=None, max_length=30)
    address: str | None = None
    facebook: str | None = Field(default=None, max_length=255)
    instagram: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=255)
    terms_and_conditions: str | None = None
    privacy_policy: str | None = None


class SystemSettingsResponse(SystemSettingsBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    updated_at: datetime
