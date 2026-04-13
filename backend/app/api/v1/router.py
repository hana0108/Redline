from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    branches,
    bulk,
    cache,
    clients,
    documents,
    health,
    reports,
    roles,
    sales,
    search,
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
api_router.include_router(documents.router)
api_router.include_router(bulk.router)
api_router.include_router(health.router)
api_router.include_router(search.router)
api_router.include_router(cache.router)
api_router.include_router(settings.router)
api_router.include_router(reports.router)
