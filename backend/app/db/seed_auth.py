from __future__ import annotations

import uuid

import app.db.base  # noqa: F401
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.enums import StatusGeneric
from app.models.role import Permission, Role, RolePermission
from app.models.settings import SystemSettings
from app.models.user import User

PERMISSIONS: list[dict[str, str]] = [
    {"code": "roles.read", "name": "Ver roles", "description": "Permite consultar roles"},
    {
        "code": "roles.write",
        "name": "Gestionar roles",
        "description": "Permite crear y editar roles",
    },
    {"code": "users.read", "name": "Ver usuarios", "description": "Permite consultar usuarios"},
    {
        "code": "users.write",
        "name": "Gestionar usuarios",
        "description": "Permite crear y editar usuarios",
    },
    {
        "code": "branches.read",
        "name": "Ver sucursales",
        "description": "Permite consultar sucursales",
    },
    {
        "code": "branches.write",
        "name": "Gestionar sucursales",
        "description": "Permite crear y editar sucursales",
    },
    {
        "code": "vehicles.read",
        "name": "Ver vehículos",
        "description": "Permite consultar vehículos",
    },
    {
        "code": "vehicles.write",
        "name": "Gestionar vehículos",
        "description": "Permite crear y editar vehículos",
    },
    {"code": "clients.read", "name": "Ver clientes", "description": "Permite consultar clientes"},
    {
        "code": "clients.write",
        "name": "Gestionar clientes",
        "description": "Permite crear y editar clientes",
    },
    {"code": "sales.read", "name": "Ver ventas", "description": "Permite consultar ventas"},
    {"code": "sales.write", "name": "Gestionar ventas", "description": "Permite registrar ventas"},
    {"code": "reports.read", "name": "Ver reportes", "description": "Permite consultar reportes"},
    {
        "code": "settings.read",
        "name": "Ver configuración",
        "description": "Permite consultar configuración",
    },
    {
        "code": "settings.write",
        "name": "Gestionar configuración",
        "description": "Permite editar configuración",
    },
]

ROLE_DEFINITIONS: list[dict[str, object]] = [
    {
        "code": "admin",
        "name": "Admin",
        "description": "Administrador del sistema",
        "permissions": [item["code"] for item in PERMISSIONS],
    },
    {
        "code": "manager",
        "name": "Gerente",
        "description": "Gerencia y reportes",
        "permissions": [
            "users.read",
            "branches.read",
            "vehicles.read",
            "clients.read",
            "sales.read",
            "reports.read",
            "settings.read",
        ],
    },
    {
        "code": "seller",
        "name": "Vendedor",
        "description": "Gestión comercial",
        "permissions": [
            "vehicles.read",
            "clients.read",
            "clients.write",
            "sales.read",
            "sales.write",
        ],
    },
    {
        "code": "inventory",
        "name": "Inventario",
        "description": "Gestión de inventario",
        "permissions": [
            "branches.read",
            "vehicles.read",
            "vehicles.write",
        ],
    },
]


def get_or_create_permission(
    db: Session, code: str, name: str, description: str | None
) -> Permission:
    permission = db.scalar(select(Permission).where(Permission.code == code))
    if permission:
        changed = False
        if permission.name != name:
            permission.name = name
            changed = True
        if permission.description != description:
            permission.description = description
            changed = True
        if changed:
            db.add(permission)
            db.flush()
        return permission

    permission = Permission(id=uuid.uuid4(), code=code, name=name, description=description)
    db.add(permission)
    db.flush()
    return permission


def get_or_create_role(db: Session, code: str, name: str, description: str | None) -> Role:
    role = db.scalar(select(Role).where(Role.code == code))
    if role:
        changed = False
        if role.name != name:
            role.name = name
            changed = True
        if role.description != description:
            role.description = description
            changed = True
        if changed:
            db.add(role)
            db.flush()
        return role

    role = Role(id=uuid.uuid4(), code=code, name=name, description=description)
    db.add(role)
    db.flush()
    return role


def ensure_role_permission(db: Session, role_id: uuid.UUID, permission_id: uuid.UUID) -> None:
    existing = db.scalar(
        select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
        )
    )
    if existing:
        return
    db.add(RolePermission(role_id=role_id, permission_id=permission_id))
    db.flush()


def ensure_system_settings(db: Session) -> None:
    settings = db.scalar(select(SystemSettings))
    if settings:
        return
    db.add(SystemSettings(business_name="Redline"))
    db.flush()


def ensure_admin_user(db: Session, admin_role: Role) -> None:
    user = db.scalar(select(User).where(User.email == "admin@redline.com"))
    if user:
        changed = False
        if user.role_id != admin_role.id:
            user.role_id = admin_role.id
            changed = True
        if getattr(user, "status", None) != StatusGeneric.ACTIVE:
            user.status = StatusGeneric.ACTIVE
            changed = True
        if changed:
            db.add(user)
            db.flush()
        return

    db.add(
        User(
            role_id=admin_role.id,
            full_name="Administrador Inicial",
            email="admin@redline.com",
            phone=None,
            password_hash=get_password_hash("Admin123*"),
            status=StatusGeneric.ACTIVE,
            last_login_at=None,
        )
    )
    db.flush()


def run() -> None:
    db = SessionLocal()
    try:
        permission_map: dict[str, Permission] = {}
        for item in PERMISSIONS:
            permission = get_or_create_permission(
                db, item["code"], item["name"], item.get("description")
            )
            permission_map[item["code"]] = permission

        role_map: dict[str, Role] = {}
        for item in ROLE_DEFINITIONS:
            role = get_or_create_role(
                db, str(item["code"]), str(item["name"]), item.get("description")
            )
            role_map[str(item["code"])] = role
            for permission_code in item["permissions"]:
                ensure_role_permission(db, role.id, permission_map[str(permission_code)].id)

        ensure_system_settings(db)
        ensure_admin_user(db, role_map["admin"])

        db.commit()
        print("Seed completado correctamente.")
        print("Usuario inicial: admin@redline.com")
        print("Clave inicial: Admin123*")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
