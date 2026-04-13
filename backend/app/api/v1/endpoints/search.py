from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import distinct, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.search import (
    ClientSearchFilter,
    ClientSearchResponse,
    UnifiedSearchResponse,
    VehicleSearchFilter,
    VehicleSearchResponse,
)
from app.services.search_service import search_service

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/vehicles", response_model=VehicleSearchResponse)
async def search_vehicles(
    db: Annotated[Session, Depends(get_db)],
    q: Annotated[str, Query(description="Search query", min_length=1)],
    branch_id: Annotated[UUID | None, Query(description="Filter by branch UUID")] = None,
    status: Annotated[str | None, Query(description="Filter by vehicle status")] = None,
    price_min: Annotated[float | None, Query(description="Minimum price", ge=0)] = None,
    price_max: Annotated[float | None, Query(description="Maximum price", ge=0)] = None,
    year_min: Annotated[int | None, Query(description="Minimum year", ge=1900, le=2100)] = None,
    year_max: Annotated[int | None, Query(description="Maximum year", ge=1900, le=2100)] = None,
    fuel_type: Annotated[str | None, Query(description="Filter by fuel type")] = None,
    transmission: Annotated[str | None, Query(description="Filter by transmission")] = None,
    vehicle_type: Annotated[str | None, Query(description="Filter by vehicle type")] = None,
    limit: Annotated[int, Query(description="Results per page", ge=1, le=100)] = 50,
    offset: Annotated[int, Query(description="Results offset", ge=0)] = 0,
    facets: Annotated[bool, Query(description="Include search facets")] = False,
) -> VehicleSearchResponse:
    """Advanced vehicle search with full-text search and filters"""
    filters = VehicleSearchFilter(
        query=q,
        branch_id=branch_id,
        status=status,
        price_min=price_min,
        price_max=price_max,
        year_min=year_min,
        year_max=year_max,
        fuel_type=fuel_type,
        transmission=transmission,
        vehicle_type=vehicle_type,
        limit=limit,
        offset=offset,
    )

    return await search_service.search_vehicles(db, filters, include_facets=facets)


@router.get("/clients", response_model=ClientSearchResponse)
async def search_clients(
    db: Annotated[Session, Depends(get_db)],
    q: Annotated[str, Query(description="Search query", min_length=1)],
    document_type: Annotated[str | None, Query(description="Filter by document type")] = None,
    limit: Annotated[int, Query(description="Results per page", ge=1, le=100)] = 50,
    offset: Annotated[int, Query(description="Results offset", ge=0)] = 0,
) -> ClientSearchResponse:
    """Advanced client search with full-text search and filters"""
    filters = ClientSearchFilter(
        query=q,
        document_type=document_type,
        limit=limit,
        offset=offset,
    )

    return await search_service.search_clients(db, filters)


@router.get("", response_model=UnifiedSearchResponse)
async def unified_search(
    db: Annotated[Session, Depends(get_db)],
    q: Annotated[str, Query(description="Search query across all entities", min_length=1)],
    entity_type: Annotated[
        str | None,
        Query(
            description="Limit search to specific entity type",
            regex="^(vehicles|clients|sales|users)$",
        ),
    ] = None,
    limit_per_type: Annotated[int, Query(description="Results per entity type", ge=1, le=50)] = 10,
) -> UnifiedSearchResponse:
    """Unified search across vehicles, clients, sales, and users"""
    return await search_service.unified_search(
        db=db, query=q, entity_type=entity_type, limit_per_type=limit_per_type
    )


@router.get("/suggest")
async def search_suggestions(
    db: Annotated[Session, Depends(get_db)],
    q: Annotated[str, Query(description="Partial search query", min_length=1, max_length=50)],
    entity_type: Annotated[
        str | None, Query(description="Entity type for suggestions", regex="^(vehicles|clients)$")
    ] = None,
    limit: Annotated[int, Query(description="Number of suggestions", ge=1, le=20)] = 10,
) -> dict:
    """Get search suggestions based on partial query"""
    # This is a simplified implementation
    # In production, you might want to use a dedicated suggestions index

    suggestions = {"vehicles": [], "clients": [], "query": q}

    if not entity_type or entity_type == "vehicles":
        # Get vehicle brand/model suggestions
        from app.models.vehicle import Vehicle

        brands = db.scalars(
            select(distinct(Vehicle.brand)).where(Vehicle.brand.ilike(f"{q}%")).limit(limit)
        ).all()

        models = db.scalars(
            select(distinct(Vehicle.model)).where(Vehicle.model.ilike(f"{q}%")).limit(limit)
        ).all()

        suggestions["vehicles"] = list(set(brands + models))[:limit]

    if not entity_type or entity_type == "clients":
        # Get client name suggestions
        from app.models.client import Client

        names = db.scalars(
            select(Client.full_name).where(Client.full_name.ilike(f"{q}%")).limit(limit)
        ).all()

        suggestions["clients"] = list(names)

    return suggestions
