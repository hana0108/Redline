from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class SearchFilter(BaseModel):
    """Base search filter model"""

    query: str = Field(..., min_length=1, description="Search query text")
    limit: int = Field(50, ge=1, le=100, description="Maximum results to return")
    offset: int = Field(0, ge=0, description="Number of results to skip")


class VehicleSearchFilter(SearchFilter):
    """Advanced search filters for vehicles"""

    branch_id: Optional[UUID] = Field(None, description="Filter by branch")
    status: Optional[str] = Field(None, description="Filter by vehicle status")
    price_min: Optional[float] = Field(None, ge=0, description="Minimum price filter")
    price_max: Optional[float] = Field(None, ge=0, description="Maximum price filter")
    year_min: Optional[int] = Field(None, ge=1900, le=2100, description="Minimum year filter")
    year_max: Optional[int] = Field(None, ge=1900, le=2100, description="Maximum year filter")
    fuel_type: Optional[str] = Field(None, description="Filter by fuel type")
    transmission: Optional[str] = Field(None, description="Filter by transmission")
    vehicle_type: Optional[str] = Field(None, description="Filter by vehicle type")


class ClientSearchFilter(SearchFilter):
    """Advanced search filters for clients"""

    document_type: Optional[str] = Field(None, description="Filter by document type")


class SearchResult(BaseModel):
    """Base search result with relevance scoring"""

    id: UUID
    relevance: float = Field(..., description="Search relevance score (0-1)")


class VehicleSearchResult(SearchResult):
    """Vehicle search result"""

    brand: str
    model: str
    vehicle_year: int
    price: float
    vin: str
    plate: Optional[str]
    status: str
    branch_name: Optional[str] = Field(None, description="Branch name for display")


class ClientSearchResult(SearchResult):
    """Client search result"""

    full_name: str
    email: str
    phone: Optional[str]
    document_number: Optional[str]
    branch_name: Optional[str] = Field(None, description="Branch name for display")


class SaleSearchResult(SearchResult):
    """Sale search result"""

    sale_date: str
    sale_price: float
    client_name: str
    vehicle_info: str  # "Brand Model Year"


class UserSearchResult(SearchResult):
    """User search result"""

    full_name: str
    email: str
    role_name: str
    branch_name: Optional[str] = Field(None, description="Branch name for display")


class UnifiedSearchResponse(BaseModel):
    """Unified search response across all entities"""

    query: str
    total_results: int
    vehicles: List[VehicleSearchResult] = Field(default_factory=list)
    clients: List[ClientSearchResult] = Field(default_factory=list)
    sales: List[SaleSearchResult] = Field(default_factory=list)
    users: List[UserSearchResult] = Field(default_factory=list)


class SearchFacets(BaseModel):
    """Search facets for filtering options"""

    statuses: List[str] = Field(default_factory=list, description="Available vehicle statuses")
    brands: List[str] = Field(default_factory=list, description="Available vehicle brands")
    fuel_types: List[str] = Field(default_factory=list, description="Available fuel types")
    transmissions: List[str] = Field(default_factory=list, description="Available transmissions")
    vehicle_types: List[str] = Field(default_factory=list, description="Available vehicle types")
    price_range: Optional[Dict[str, float]] = Field(None, description="Min/max price range")
    year_range: Optional[Dict[str, int]] = Field(None, description="Min/max year range")


class VehicleSearchResponse(BaseModel):
    """Response for vehicle search with facets"""

    results: List[VehicleSearchResult]
    total: int
    facets: Optional[SearchFacets] = None
    query: str
    filters_applied: Dict[str, Any] = Field(default_factory=dict)


class ClientSearchResponse(BaseModel):
    """Response for client search"""

    results: List[ClientSearchResult]
    total: int
    query: str
    filters_applied: Dict[str, Any] = Field(default_factory=dict)


# Configuration for OpenAPI
SearchFilter.model_rebuild()
VehicleSearchFilter.model_rebuild()
ClientSearchFilter.model_rebuild()
