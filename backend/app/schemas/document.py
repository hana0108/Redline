from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DocumentType


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    entity_type: str
    entity_id: UUID
    file_path: str
    document_type: DocumentType
    created_at: datetime
    updated_at: datetime


class DocumentCreate(BaseModel):
    entity_type: str = Field(min_length=1, max_length=50)
    entity_id: UUID
    document_type: DocumentType


class DocumentUpdate(BaseModel):
    document_type: DocumentType | None = None


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int