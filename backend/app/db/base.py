from app.db.base_class import Base

# Importar modelos para registrar metadata y relaciones.
from app.models.audit import AuditLog  # noqa: E402,F401
from app.models.branch import Branch  # noqa: E402,F401
from app.models.catalog import (  # noqa: E402,F401
    FuelTypeCatalog,
    TransmissionCatalog,
    VehicleBrand,
    VehicleColorCatalog,
    VehicleModelCatalog,
    VehicleTypeCatalog,
)
from app.models.client import Client, ClientPreference  # noqa: E402,F401
from app.models.document import Document  # noqa: E402,F401
from app.models.role import Permission, Role, RolePermission  # noqa: E402,F401
from app.models.sale import Sale  # noqa: E402,F401
from app.models.settings import SystemSettings  # noqa: E402,F401
from app.models.user import User, UserBranchAccess  # noqa: E402,F401
from app.models.vehicle import Vehicle, VehicleImage, VehicleStatusHistory  # noqa: E402,F401
