from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import bad_request, not_found
from app.models.branch import Branch
from app.models.client import Client
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.sale import Sale
from app.models.enums import VehicleStatus


@dataclass(slots=True)
class CommercialRefs:
    vehicle: Vehicle
    client: Client
    branch: Branch | None
    seller_user: User | None


def get_vehicle_or_404(db: Session, vehicle_id: UUID) -> Vehicle:
    vehicle = db.get(Vehicle, vehicle_id)
    if not vehicle:
        raise not_found("Vehículo no encontrado")
    return vehicle


def get_sale_or_404(db: Session, sale_id: UUID) -> Sale:
    sale = db.get(Sale, sale_id)
    if not sale:
        raise not_found("Venta no encontrada")
    return sale


def validate_commercial_refs(
    db: Session,
    *,
    vehicle_id: UUID,
    client_id: UUID,
    branch_id: UUID | None = None,
    seller_user_id: UUID | None = None,
) -> CommercialRefs:
    vehicle = db.get(Vehicle, vehicle_id)
    if not vehicle:
        raise not_found("Vehículo no encontrado")

    client = db.get(Client, client_id)
    if not client:
        raise not_found("Cliente no encontrado")

    branch = None
    if branch_id is not None:
        branch = db.get(Branch, branch_id)
        if not branch:
            raise not_found("Sucursal no encontrada")

    seller_user = None
    if seller_user_id is not None:
        seller_user = db.get(User, seller_user_id)
        if not seller_user:
            raise not_found("Vendedor no encontrado")

    return CommercialRefs(vehicle=vehicle, client=client, branch=branch, seller_user=seller_user)


def ensure_vehicle_sellable(db: Session, vehicle: Vehicle) -> None:  # noqa: ARG001
    if vehicle.status == VehicleStatus.VENDIDO:
        raise bad_request("El vehículo ya fue vendido")
    if vehicle.status == VehicleStatus.RETIRADO:
        raise bad_request("El vehículo está retirado y no puede ser vendido")
