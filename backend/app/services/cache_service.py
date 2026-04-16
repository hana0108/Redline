import hashlib
import logging
from typing import Any

from app.cache.redis_cache import cache
from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """High-level cache service for common caching patterns"""

    @staticmethod
    def _make_key(*parts: Any) -> str:
        """Create a cache key from multiple parts"""
        key_parts = [str(part) for part in parts if part is not None]
        return ":".join(key_parts)

    @staticmethod
    def _hash_query(query: str, filters: dict[str, Any] | None = None) -> str:
        """Create a hash for query + filters combination"""
        content = query
        if filters:
            # Sort filters for consistent hashing
            sorted_filters = sorted(filters.items())
            content += str(sorted_filters)
        return hashlib.md5(content.encode()).hexdigest()[:8]

    async def get_or_set(
        self, key: str, getter_func, ttl: int | None = None, force_refresh: bool = False
    ) -> Any:
        """Get from cache or set if not exists"""
        if not force_refresh:
            cached_value = await cache.get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit for key: {key}")
                return cached_value

        logger.debug(f"Cache miss for key: {key}, calling getter function")
        value = await getter_func()

        if value is not None:
            await cache.set(key, value, ttl)

        return value

    # Report caching methods
    async def get_dashboard_data(self, force_refresh: bool = False):
        """Cache dashboard report data"""
        key = self._make_key("report", "dashboard")
        ttl = settings.REDIS_CACHE_TTL_REPORTS

        async def _get_dashboard():
            from app.services.report_service import report_service

            return await report_service.get_dashboard_data()

        return await self.get_or_set(key, _get_dashboard, ttl, force_refresh)

    async def get_inventory_summary(self, force_refresh: bool = False):
        """Cache inventory summary report"""
        key = self._make_key("report", "inventory", "summary")
        ttl = settings.REDIS_CACHE_TTL_REPORTS

        async def _get_inventory_summary():
            from app.services.report_service import report_service

            return await report_service.get_inventory_summary()

        return await self.get_or_set(key, _get_inventory_summary, ttl, force_refresh)

    async def get_sales_summary(self, force_refresh: bool = False):
        """Cache sales summary report"""
        key = self._make_key("report", "sales", "summary")
        ttl = settings.REDIS_CACHE_TTL_REPORTS

        async def _get_sales_summary():
            from app.services.report_service import report_service

            return await report_service.get_sales_summary()

        return await self.get_or_set(key, _get_sales_summary, ttl, force_refresh)

    async def get_inventory_rows(self, force_refresh: bool = False):
        """Cache inventory rows for export"""
        key = self._make_key("report", "inventory", "rows")
        ttl = settings.REDIS_CACHE_TTL_REPORTS

        async def _get_inventory_rows():
            from app.services.report_service import report_service

            return await report_service.get_inventory_rows()

        return await self.get_or_set(key, _get_inventory_rows, ttl, force_refresh)

    async def get_sales_rows(self, force_refresh: bool = False):
        """Cache sales rows for export"""
        key = self._make_key("report", "sales", "rows")
        ttl = settings.REDIS_CACHE_TTL_REPORTS

        async def _get_sales_rows():
            from app.services.report_service import report_service

            return await report_service.get_sales_rows()

        return await self.get_or_set(key, _get_sales_rows, ttl, force_refresh)

    # Entity caching methods
    async def get_client(self, client_id: str, force_refresh: bool = False):
        """Cache individual client data"""
        key = self._make_key("client", client_id)
        ttl = settings.REDIS_CACHE_TTL_ENTITIES

        async def _get_client():
            from app.db.session import SessionLocal
            from app.services.client_service import client_service

            db = SessionLocal()
            try:
                client = await client_service.get_client_by_id(db, client_id)
                return client.model_dump() if client else None
            finally:
                db.close()

        return await self.get_or_set(key, _get_client, ttl, force_refresh)

    async def get_vehicle(self, vehicle_id: str, force_refresh: bool = False):
        """Cache individual vehicle data"""
        key = self._make_key("vehicle", vehicle_id)
        ttl = settings.REDIS_CACHE_TTL_ENTITIES

        async def _get_vehicle():
            from app.db.session import SessionLocal
            from app.services.vehicle_service import vehicle_service

            db = SessionLocal()
            try:
                vehicle = await vehicle_service.get_vehicle_by_id(db, vehicle_id)
                return vehicle.model_dump() if vehicle else None
            finally:
                db.close()

        return await self.get_or_set(key, _get_vehicle, ttl, force_refresh)

    async def get_sale(self, sale_id: str, force_refresh: bool = False):
        """Cache individual sale data"""
        key = self._make_key("sale", sale_id)
        ttl = settings.REDIS_CACHE_TTL_ENTITIES

        async def _get_sale():
            from app.db.session import SessionLocal
            from app.models.sale import Sale

            db = SessionLocal()
            try:
                sale = db.get(Sale, sale_id)
                if not sale:
                    return None

                return {
                    "id": str(sale.id),
                    "vehicle_id": str(sale.vehicle_id),
                    "client_id": str(sale.client_id),
                    "seller_user_id": str(sale.seller_user_id) if sale.seller_user_id else None,
                    "branch_id": str(sale.branch_id) if sale.branch_id else None,
                    "sale_date": sale.sale_date.isoformat() if sale.sale_date else None,
                    "sale_price": float(sale.sale_price),
                    "cost": float(sale.cost) if sale.cost is not None else None,
                    "profit": float(sale.profit) if sale.profit is not None else None,
                    "payment_method": sale.payment_method.value
                    if hasattr(sale.payment_method, "value")
                    else str(sale.payment_method),
                    "status": sale.status.value
                    if hasattr(sale.status, "value")
                    else str(sale.status),
                    "notes": sale.notes,
                }
            finally:
                db.close()

        return await self.get_or_set(key, _get_sale, ttl, force_refresh)

    async def get_settings(self, force_refresh: bool = False):
        """Cache application settings"""
        key = self._make_key("settings")
        ttl = settings.REDIS_CACHE_TTL_SETTINGS

        async def _get_settings():
            from app.db.session import SessionLocal
            from app.services.settings_service import get_settings as _db_get_settings

            db = SessionLocal()
            try:
                s = _db_get_settings(db)
                if s is None:
                    return None
                # Convert ORM object to plain dict — str() handles UUID/datetime
                return {
                    col.name: (
                        str(getattr(s, col.name)) if getattr(s, col.name) is not None else None
                    )
                    for col in type(s).__table__.columns
                }
            finally:
                db.close()

        return await self.get_or_set(key, _get_settings, ttl, force_refresh)

    # List caching methods
    async def get_clients_list(self, force_refresh: bool = False):
        """Cache clients list (when no filters)"""
        key = self._make_key("clients", "list")
        ttl = settings.REDIS_CACHE_TTL_LISTS

        async def _get_clients_list():
            from app.db.session import SessionLocal
            from app.services.client_service import client_service

            db = SessionLocal()
            try:
                clients = await client_service.get_clients(db)
                return [client.model_dump() for client in clients]
            finally:
                db.close()

        return await self.get_or_set(key, _get_clients_list, ttl, force_refresh)

    async def get_vehicles_list(self, force_refresh: bool = False):
        """Cache vehicles list (when no filters)"""
        key = self._make_key("vehicles", "list")
        ttl = settings.REDIS_CACHE_TTL_LISTS

        async def _get_vehicles_list():
            from app.db.session import SessionLocal
            from app.services.vehicle_service import vehicle_service

            db = SessionLocal()
            try:
                vehicles = await vehicle_service.get_vehicles(db)
                return [vehicle.model_dump() for vehicle in vehicles]
            finally:
                db.close()

        return await self.get_or_set(key, _get_vehicles_list, ttl, force_refresh)

    # Search caching methods
    async def get_vehicle_search(
        self, query: str, filters: dict[str, Any], force_refresh: bool = False
    ):
        """Cache vehicle search results"""
        query_hash = self._hash_query(query, filters)
        key = self._make_key("search", "vehicles", query_hash)
        ttl = settings.REDIS_CACHE_TTL_SEARCH

        async def _get_vehicle_search():
            from app.db.session import SessionLocal
            from app.schemas.search import VehicleSearchFilter
            from app.services.search_service import search_service

            db = SessionLocal()
            try:
                search_filters = VehicleSearchFilter(**filters, query=query)
                result = await search_service.search_vehicles(db, search_filters)
                return result.model_dump()
            finally:
                db.close()

        return await self.get_or_set(key, _get_vehicle_search, ttl, force_refresh)

    async def get_client_search(
        self, query: str, filters: dict[str, Any], force_refresh: bool = False
    ):
        """Cache client search results"""
        query_hash = self._hash_query(query, filters)
        key = self._make_key("search", "clients", query_hash)
        ttl = settings.REDIS_CACHE_TTL_SEARCH

        async def _get_client_search():
            from app.db.session import SessionLocal
            from app.schemas.search import ClientSearchFilter
            from app.services.search_service import search_service

            db = SessionLocal()
            try:
                search_filters = ClientSearchFilter(**filters, query=query)
                result = await search_service.search_clients(db, search_filters)
                return result.model_dump()
            finally:
                db.close()

        return await self.get_or_set(key, _get_client_search, ttl, force_refresh)

    # Cache invalidation methods
    async def invalidate_reports(self):
        """Invalidate all report caches"""
        patterns = [
            "report:*",
        ]
        total_deleted = 0
        for pattern in patterns:
            total_deleted += await cache.delete_pattern(pattern)

        if total_deleted > 0:
            logger.info(f"Invalidated {total_deleted} report cache entries")

    async def invalidate_entity(self, entity_type: str, entity_id: str):
        """Invalidate specific entity cache"""
        key = self._make_key(entity_type, entity_id)
        await cache.delete(key)
        logger.debug(f"Invalidated cache for {entity_type}:{entity_id}")

    async def invalidate_entity_list(self, entity_type: str):
        """Invalidate entity list cache"""
        key = self._make_key(entity_type, "list")
        await cache.delete(key)
        logger.debug(f"Invalidated cache for {entity_type} list")

    async def invalidate_search_results(self, entity_type: str):
        """Invalidate search results for entity type"""
        pattern = f"search:{entity_type}:*"
        deleted = await cache.delete_pattern(pattern)
        if deleted > 0:
            logger.debug(f"Invalidated {deleted} search cache entries for {entity_type}")

    async def invalidate_sale_related_caches(self):
        """Invalidate all caches affected by sale changes"""
        await self.invalidate_reports()
        await self.invalidate_entity_list("sales")
        await self.invalidate_search_results("sales")

    async def invalidate_vehicle_related_caches(self, vehicle_id: str | None = None):
        """Invalidate caches affected by vehicle changes"""
        await self.invalidate_reports()
        await self.invalidate_entity_list("vehicles")
        await self.invalidate_search_results("vehicles")
        if vehicle_id:
            await self.invalidate_entity("vehicle", vehicle_id)

    async def invalidate_client_related_caches(self, client_id: str | None = None):
        """Invalidate caches affected by client changes"""
        await self.invalidate_reports()
        await self.invalidate_entity_list("clients")
        await self.invalidate_search_results("clients")
        if client_id:
            await self.invalidate_entity("client", client_id)


# Global cache service instance
cache_service = CacheService()
