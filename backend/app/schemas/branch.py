from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.enums import StatusGeneric


class BranchBase(BaseModel):
    name: str
    address: str | None = None
    phone: str | None = None
    email: EmailStr | None = None


class BranchCreate(BranchBase):
    pass


class BranchUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    status: StatusGeneric | None = None


class BranchResponse(BranchBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: StatusGeneric
    created_at: datetime
    updated_at: datetime
