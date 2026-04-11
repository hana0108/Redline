from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import StatusGeneric


class UserCreate(BaseModel):
    role_id: UUID
    full_name: str = Field(min_length=3, max_length=180)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    password: str = Field(min_length=8, max_length=128)
    status: StatusGeneric = StatusGeneric.ACTIVE
    branch_ids: list[UUID] = []


class UserUpdate(BaseModel):
    role_id: UUID | None = None
    full_name: str | None = Field(default=None, min_length=3, max_length=180)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    status: StatusGeneric | None = None


class UserBranchesUpdate(BaseModel):
    branch_ids: list[UUID]


class UserStatusUpdate(BaseModel):
    status: StatusGeneric


class RoleMini(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: RoleMini
    full_name: str
    email: EmailStr
    phone: str | None = None
    status: StatusGeneric
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    branch_ids: list[UUID] = []
