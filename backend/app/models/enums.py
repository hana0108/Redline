from __future__ import annotations

from enum import Enum


class StatusGeneric(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class VehicleStatus(str, Enum):
    DISPONIBLE = "disponible"
    RESERVADO = "reservado"
    VENDIDO = "vendido"
    EN_PROCESO = "en_proceso"
    RETIRADO = "retirado"


class SaleStatus(str, Enum):
    COMPLETADA = "completada"
    ANULADA = "anulada"


class DocumentType(str, Enum):
    VENTA_PDF = "venta_pdf"
    OTRO = "otro"


class AuditAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    STATUS_CHANGE = "status_change"
    SALE = "sale"
