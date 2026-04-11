from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.sql_enums import pg_enum
from app.models.enums import SaleStatus
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.branch import Branch
    from app.models.client import Client
    from app.models.user import User
    from app.models.vehicle import Vehicle


class Sale(Base, TimestampMixin):
    __tablename__ = "sales"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False, unique=True
    )
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    seller_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=True)
    sale_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    sale_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    profit: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    payment_method: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[SaleStatus] = mapped_column(
        pg_enum(SaleStatus, "sale_status"),
        nullable=False,
        default=SaleStatus.COMPLETADA,
        server_default=SaleStatus.COMPLETADA.value,
    )
    notes: Mapped[str | None] = mapped_column(Text())

    vehicle: Mapped["Vehicle"] = relationship("Vehicle")
    client: Mapped["Client"] = relationship("Client")
    seller_user: Mapped["User | None"] = relationship("User")
    branch: Mapped["Branch | None"] = relationship("Branch", back_populates="sales")
