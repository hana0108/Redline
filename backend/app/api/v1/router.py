from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    branches,
    clients,
    reports,
    roles,
    sales,
    settings,
    users,
    vehicles,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(roles.router)
api_router.include_router(users.router)
api_router.include_router(branches.router)
api_router.include_router(vehicles.router)
api_router.include_router(clients.router)
api_router.include_router(sales.router)
api_router.include_router(settings.router)
api_router.include_router(reports.router)
