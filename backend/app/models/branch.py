from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.sql_enums import pg_enum
from app.models.enums import StatusGeneric
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.sale import Sale
    from app.models.user import UserBranchAccess
    from app.models.vehicle import Vehicle


class Branch(Base, TimestampMixin):
    __tablename__ = "branches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    status: Mapped[StatusGeneric] = mapped_column(
        pg_enum(StatusGeneric, "status_generic"),
        nullable=False,
        default=StatusGeneric.ACTIVE,
        server_default=StatusGeneric.ACTIVE.value,
    )

    vehicles: Mapped[list["Vehicle"]] = relationship("Vehicle", back_populates="branch")
    sales: Mapped[list["Sale"]] = relationship("Sale", back_populates="branch")
    user_links: Mapped[list["UserBranchAccess"]] = relationship(
        "UserBranchAccess",
        back_populates="branch",
        cascade="all, delete-orphan",
    )
