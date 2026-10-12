from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PlaceItem(BaseModel):
    place_id: Optional[int] = None
    osm_id: Optional[int] = None
    osm_type: Optional[str] = None
    display_name: str
    lat: float
    lon: float
    category: Optional[str] = None
    type: Optional[str] = None
    importance: Optional[float] = None
    boundingbox: Optional[List[str]] = None


class MapSearchResponse(BaseModel):
    query: str
    count: int
    results: List[PlaceItem]
    attribution: str = "© OpenStreetMap contributors"


class MapReverseResponse(BaseModel):
    place_id: Optional[int] = None
    osm_id: Optional[int] = None
    osm_type: Optional[str] = None
    lat: float
    lon: float
    display_name: str
    address: Dict[str, Any] = Field(default_factory=dict)
    attribution: str = "© OpenStreetMap contributors"
