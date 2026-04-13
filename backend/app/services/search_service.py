import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select, text, and_, or_, desc
from sqlalchemy.orm import Session, joinedload

from app.models.branch import Branch
from app.models.client import Client
from app.models.sale import Sale
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.search import (
    ClientSearchFilter,
    ClientSearchResponse,
    ClientSearchResult,
    SaleSearchResult,
    SearchFacets,
    UnifiedSearchResponse,
    UserSearchResult,
    VehicleSearchFilter,
    VehicleSearchResponse,
    VehicleSearchResult,
)

logger = logging.getLogger(__name__)


class SearchService:
    """Advanced search service using PostgreSQL full-text search"""

    def __init__(self):
        self.default_limit = 50
        self.max_limit = 100

    async def search_vehicles(
        self,
        db: Session,
        filters: VehicleSearchFilter,
        include_facets: bool = False
    ) -> VehicleSearchResponse:
        """Advanced vehicle search with FTS and filters"""
        logger.debug(f"Searching vehicles with query: {filters.query}")

        # Build base query with FTS
        base_query = self._build_vehicle_fts_query(db, filters.query)

        # Apply filters
        base_query = self._apply_vehicle_filters(base_query, filters)

        # Get total count
        total_query = select(func.count()).select_from(base_query.subquery())
        total = db.scalar(total_query) or 0

        # Apply pagination and ordering
        query = base_query.order_by(
            text("relevance DESC"),
            Vehicle.created_at.desc()
        ).limit(filters.limit).offset(filters.offset)

        # Execute query with joins for branch info
        results = db.execute(
            query.options(joinedload(Vehicle.branch))
        ).unique().scalars().all()

        # Convert to response format
        search_results = []
        for vehicle in results:
            # Get relevance score from the query result
            relevance = getattr(vehicle, '_relevance', 0.0)

            search_results.append(VehicleSearchResult(
                id=vehicle.id,
                relevance=relevance,
                brand=vehicle.brand,
                model=vehicle.model,
                vehicle_year=vehicle.vehicle_year,
                price=vehicle.price,
                vin=vehicle.vin,
                plate=vehicle.plate,
                status=vehicle.status,
                branch_name=vehicle.branch.name if vehicle.branch else None
            ))

        # Get facets if requested
        facets = None
        if include_facets and filters.query:
            facets = self._get_vehicle_facets(db, filters.query)

        return VehicleSearchResponse(
            results=search_results,
            total=total,
            facets=facets,
            query=filters.query,
            filters_applied=self._get_applied_filters(filters)
        )

    async def search_clients(
        self,
        db: Session,
        filters: ClientSearchFilter
    ) -> ClientSearchResponse:
        """Advanced client search with FTS and filters"""
        logger.debug(f"Searching clients with query: {filters.query}")

        # Build base query with FTS
        base_query = self._build_client_fts_query(db, filters.query)

        # Apply filters
        base_query = self._apply_client_filters(base_query, filters)

        # Get total count
        total_query = select(func.count()).select_from(base_query.subquery())
        total = db.scalar(total_query) or 0

        # Apply pagination and ordering
        query = base_query.order_by(
            text("relevance DESC"),
            Client.created_at.desc()
        ).limit(filters.limit).offset(filters.offset)

        # Execute query
        results = db.execute(query).scalars().all()

        # Convert to response format
        search_results = []
        for client in results:
            relevance = getattr(client, '_relevance', 0.0)

            search_results.append(ClientSearchResult(
                id=client.id,
                relevance=relevance,
                full_name=client.full_name,
                email=client.email,
                phone=client.phone,
                document_number=client.document_number,
                branch_name=None  # Clients don't have branch relationship
            ))

        return ClientSearchResponse(
            results=search_results,
            total=total,
            query=filters.query,
            filters_applied=self._get_applied_filters(filters)
        )

    async def unified_search(
        self,
        db: Session,
        query: str,
        entity_type: Optional[str] = None,
        limit_per_type: int = 10
    ) -> UnifiedSearchResponse:
        """Unified search across all entities"""
        logger.debug(f"Unified search: {query}, entity_type: {entity_type}")

        results = UnifiedSearchResponse(query=query, total_results=0)
        total_results = 0

        # Search vehicles
        if not entity_type or entity_type == "vehicles":
            try:
                vehicle_filters = VehicleSearchFilter(query=query, limit=limit_per_type)
                vehicle_response = await self.search_vehicles(db, vehicle_filters)
                results.vehicles = vehicle_response.results
                total_results += vehicle_response.total
            except Exception as e:
                logger.warning(f"Vehicle search failed: {e}")

        # Search clients
        if not entity_type or entity_type == "clients":
            try:
                client_filters = ClientSearchFilter(query=query, limit=limit_per_type)
                client_response = await self.search_clients(db, client_filters)
                results.clients = client_response.results
                total_results += client_response.total
            except Exception as e:
                logger.warning(f"Client search failed: {e}")

        # Search sales (join-based search)
        if not entity_type or entity_type == "sales":
            try:
                results.sales = await self._search_sales(db, query, limit_per_type)
                total_results += len(results.sales)
            except Exception as e:
                logger.warning(f"Sale search failed: {e}")

        # Search users
        if not entity_type or entity_type == "users":
            try:
                results.users = await self._search_users(db, query, limit_per_type)
                total_results += len(results.users)
            except Exception as e:
                logger.warning(f"User search failed: {e}")

        results.total_results = total_results
        return results

    def _build_vehicle_fts_query(self, db: Session, query_text: str):
        """Build FTS query for vehicles"""
        # For now, use ILIKE fallback until FTS indexes are added
        # TODO: Replace with proper FTS when search_vector column is added
        search_terms = [f"%{term}%" for term in query_text.split()]

        conditions = []
        for term in search_terms:
            conditions.append(
                or_(
                    Vehicle.brand.ilike(term),
                    Vehicle.model.ilike(term),
                    Vehicle.vin.ilike(term),
                    Vehicle.plate.ilike(term),
                    Vehicle.color.ilike(term),
                    Vehicle.description.ilike(term),
                )
            )

        return select(Vehicle).where(and_(*conditions))

    def _build_client_fts_query(self, db: Session, query_text: str):
        """Build FTS query for clients"""
        # For now, use ILIKE fallback until FTS indexes are added
        search_terms = [f"%{term}%" for term in query_text.split()]

        conditions = []
        for term in search_terms:
            conditions.append(
                or_(
                    Client.full_name.ilike(term),
                    Client.email.ilike(term),
                    Client.phone.ilike(term),
                    Client.document_number.ilike(term),
                    Client.address.ilike(term),
                )
            )

        return select(Client).where(and_(*conditions))

    def _apply_vehicle_filters(self, query, filters: VehicleSearchFilter):
        """Apply filters to vehicle query"""
        if filters.branch_id:
            query = query.where(Vehicle.branch_id == filters.branch_id)
        if filters.status:
            query = query.where(Vehicle.status == filters.status)
        if filters.price_min is not None:
            query = query.where(Vehicle.price >= filters.price_min)
        if filters.price_max is not None:
            query = query.where(Vehicle.price <= filters.price_max)
        if filters.year_min is not None:
            query = query.where(Vehicle.vehicle_year >= filters.year_min)
        if filters.year_max is not None:
            query = query.where(Vehicle.vehicle_year <= filters.year_max)
        if filters.fuel_type:
            query = query.where(Vehicle.fuel_type == filters.fuel_type)
        if filters.transmission:
            query = query.where(Vehicle.transmission == filters.transmission)
        if filters.vehicle_type:
            query = query.where(Vehicle.vehicle_type == filters.vehicle_type)

        return query

    def _apply_client_filters(self, query, filters: ClientSearchFilter):
        """Apply filters to client query"""
        if filters.document_type:
            query = query.where(Client.document_type == filters.document_type)

        return query

    def _get_vehicle_facets(self, db: Session, query_text: str) -> SearchFacets:
        """Get available filter options for vehicle search results"""
        # Get base query for facets
        base_query = self._build_vehicle_fts_query(db, query_text)

        facets = SearchFacets()

        # Get distinct values for each facet
        facets.statuses = db.scalars(
            base_query.with_entities(func.distinct(Vehicle.status))
            .where(Vehicle.status.isnot(None))
        ).all()

        facets.brands = db.scalars(
            base_query.with_entities(func.distinct(Vehicle.brand))
            .where(Vehicle.brand.isnot(None))
        ).all()

        facets.fuel_types = db.scalars(
            base_query.with_entities(func.distinct(Vehicle.fuel_type))
            .where(Vehicle.fuel_type.isnot(None))
        ).all()

        facets.transmissions = db.scalars(
            base_query.with_entities(func.distinct(Vehicle.transmission))
            .where(Vehicle.transmission.isnot(None))
        ).all()

        facets.vehicle_types = db.scalars(
            base_query.with_entities(func.distinct(Vehicle.vehicle_type))
            .where(Vehicle.vehicle_type.isnot(None))
        ).all()

        # Get price range
        price_stats = db.execute(
            select(
                func.min(Vehicle.price).label('min_price'),
                func.max(Vehicle.price).label('max_price')
            ).select_from(base_query.subquery())
        ).first()

        if price_stats and price_stats.min_price is not None:
            facets.price_range = {
                'min': float(price_stats.min_price),
                'max': float(price_stats.max_price)
            }

        # Get year range
        year_stats = db.execute(
            select(
                func.min(Vehicle.vehicle_year).label('min_year'),
                func.max(Vehicle.vehicle_year).label('max_year')
            ).select_from(base_query.subquery())
        ).first()

        if year_stats and year_stats.min_year is not None:
            facets.year_range = {
                'min': int(year_stats.min_year),
                'max': int(year_stats.max_year)
            }

        return facets

    async def _search_sales(self, db: Session, query: str, limit: int) -> List[SaleSearchResult]:
        """Search sales by joining with vehicles and clients"""
        search_terms = [f"%{term}%" for term in query.split()]

        # Build conditions for vehicle and client search
        vehicle_conditions = []
        client_conditions = []

        for term in search_terms:
            vehicle_conditions.append(
                or_(
                    Vehicle.brand.ilike(term),
                    Vehicle.model.ilike(term),
                    Vehicle.vin.ilike(term),
                )
            )
            client_conditions.append(
                or_(
                    Client.full_name.ilike(term),
                    Client.email.ilike(term),
                    Client.document_number.ilike(term),
                )
            )

        # Search sales with joins
        query = (
            select(
                Sale.id,
                Sale.sale_date,
                Sale.sale_price,
                Client.full_name.label('client_name'),
                Vehicle.brand,
                Vehicle.model,
                Vehicle.vehicle_year,
            )
            .select_from(Sale)
            .join(Vehicle, Vehicle.id == Sale.vehicle_id)
            .join(Client, Client.id == Sale.client_id)
            .where(
                or_(
                    and_(*vehicle_conditions),
                    and_(*client_conditions)
                )
            )
            .order_by(Sale.sale_date.desc())
            .limit(limit)
        )

        results = db.execute(query).all()

        return [
            SaleSearchResult(
                id=row.id,
                relevance=0.5,  # Fixed relevance for join-based search
                sale_date=row.sale_date.isoformat(),
                sale_price=float(row.sale_price),
                client_name=row.client_name,
                vehicle_info=f"{row.brand} {row.model} {row.vehicle_year}"
            )
            for row in results
        ]

    async def _search_users(self, db: Session, query: str, limit: int) -> List[UserSearchResult]:
        """Search users with role information"""
        search_terms = [f"%{term}%" for term in query.split()]

        conditions = []
        for term in search_terms:
            conditions.append(
                or_(
                    User.full_name.ilike(term),
                    User.email.ilike(term),
                )
            )

        query = (
            select(
                User.id,
                User.full_name,
                User.email,
                User.role_id,
            )
            .where(and_(*conditions))
            .order_by(User.created_at.desc())
            .limit(limit)
        )

        results = db.execute(query).all()

        # Get role names (simplified - in production might want to join)
        role_names = {
            "admin": "Administrator",
            "manager": "Manager",
            "sales": "Sales Representative"
        }

        return [
            UserSearchResult(
                id=row.id,
                relevance=0.5,  # Fixed relevance for basic search
                full_name=row.full_name,
                email=row.email,
                role_name=role_names.get(row.role_id, "Unknown"),
                branch_name=None  # Could be added with join if needed
            )
            for row in results
        ]

    def _get_applied_filters(self, filters) -> Dict[str, Any]:
        """Extract applied filters from filter object"""
        applied = {}
        for field, value in filters.model_dump().items():
            if field != "query" and field != "limit" and field != "offset" and value is not None:
                applied[field] = value
        return applied


# Global search service instance
search_service = SearchService()