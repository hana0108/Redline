from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.sql_enums import pg_enum
from app.models.enums import StatusGeneric
from app.models.mixins import TimestampMixin


class Client(Base, TimestampMixin):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(180), nullable=False)
    document_type: Mapped[str | None] = mapped_column(String(30))
    document_number: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(150))
    phone: Mapped[str | None] = mapped_column(String(30))
    alternate_phone: Mapped[str | None] = mapped_column(String(30))
    address: Mapped[str | None] = mapped_column(Text())
    notes: Mapped[str | None] = mapped_column(Text())
    status: Mapped[StatusGeneric] = mapped_column(
        pg_enum(StatusGeneric, "status_generic"), nullable=False, default=StatusGeneric.ACTIVE, server_default=StatusGeneric.ACTIVE.value
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))

    preference: Mapped["ClientPreference | None"] = relationship(
        back_populates="client", cascade="all, delete-orphan", uselist=False
    )


class ClientPreference(Base, TimestampMixin):
    __tablename__ = "client_preferences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    preferred_brands: Mapped[list[str] | None] = mapped_column(ARRAY(String()))
    price_min: Mapped[float | None] = mapped_column(Numeric(14, 2))
    price_max: Mapped[float | None] = mapped_column(Numeric(14, 2))
    vehicle_type: Mapped[str | None] = mapped_column(String(50))
    transmission: Mapped[str | None] = mapped_column(String(50))
    fuel_type: Mapped[str | None] = mapped_column(String(50))
    color: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(Text())

    client: Mapped[Client] = relationship(back_populates="preference")
