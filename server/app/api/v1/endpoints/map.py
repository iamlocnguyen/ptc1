from fastapi import APIRouter, Depends, Query
from server.app.schemas.map import MapSearchResponse, MapReverseResponse
from server.app.services.map_service import MapService, map_service

router = APIRouter()


def get_map_service() -> MapService:
    return map_service


@router.get("/search", response_model=MapSearchResponse, summary="Tìm kiếm địa điểm (Forward Geocoding)")
async def search_places(
    q: str = Query(..., min_length=1, description="Từ khoá tìm kiếm địa điểm, địa chỉ"),
    limit: int = Query(10, ge=1, le=50, description="Số lượng kết quả tối đa trả về"),
    service: MapService = Depends(get_map_service),
) -> MapSearchResponse:
    """
    Tìm kiếm thông tin địa điểm theo tên hoặc địa chỉ sử dụng OpenStreetMap Nominatim.
    Trả về danh sách các địa điểm tìm thấy kèm theo toạ độ (lat, lon).
    """
    return await service.search(query=q, limit=limit)


@router.get("/reverse", response_model=MapReverseResponse, summary="Tra cứu địa chỉ từ toạ độ (Reverse Geocoding)")
async def reverse_geocode(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Vĩ độ (Latitude, từ -90 đến 90)"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Kinh độ (Longitude, từ -180 đến 180)"),
    service: MapService = Depends(get_map_service),
) -> MapReverseResponse:
    """
    Tra cứu thông tin địa chỉ chi tiết từ toạ độ địa lý (lat, lon) sử dụng OpenStreetMap Nominatim.
    """
    return await service.reverse(lat=lat, lon=lon)
