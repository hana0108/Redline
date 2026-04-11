from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.sql_enums import pg_enum
from app.models.enums import VehicleStatus
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.branch import Branch


class Vehicle(Base, TimestampMixin):
    __tablename__ = "vehicles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    branch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    vehicle_year: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    mileage: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    vin: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    plate: Mapped[str | None] = mapped_column(String(30))
    color: Mapped[str | None] = mapped_column(String(50))
    transmission: Mapped[str | None] = mapped_column(String(50))
    fuel_type: Mapped[str | None] = mapped_column(String(50))
    vehicle_type: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text())
    status: Mapped[VehicleStatus] = mapped_column(
        pg_enum(VehicleStatus, "vehicle_status"),
        nullable=False,
        default=VehicleStatus.DISPONIBLE,
        server_default=VehicleStatus.DISPONIBLE.value,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))

    branch: Mapped["Branch"] = relationship("Branch", back_populates="vehicles")
    images: Mapped[list["VehicleImage"]] = relationship(
        "VehicleImage", back_populates="vehicle", cascade="all, delete-orphan", order_by="VehicleImage.sort_order"
    )
    status_history: Mapped[list["VehicleStatusHistory"]] = relationship(
        "VehicleStatusHistory", back_populates="vehicle", cascade="all, delete-orphan"
    )


class VehicleImage(Base, TimestampMixin):
    __tablename__ = "vehicle_images"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(Text(), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_cover: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")

    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="images")


class VehicleStatusHistory(Base, TimestampMixin):
    __tablename__ = "vehicle_status_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    old_status: Mapped[VehicleStatus | None] = mapped_column(pg_enum(VehicleStatus, "vehicle_status"), nullable=True)
    new_status: Mapped[VehicleStatus] = mapped_column(pg_enum(VehicleStatus, "vehicle_status"), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text())

    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="status_history")
