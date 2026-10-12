from typing import Any, Dict, List, Optional
import httpx
from fastapi import HTTPException, status
from server.app.core.config import settings
from server.app.schemas.map import MapSearchResponse, MapReverseResponse, PlaceItem


class MapService:
    def __init__(
        self,
        base_url: Optional[str] = None,
        user_agent: Optional[str] = None,
        timeout: Optional[float] = None,
        client: Optional[httpx.AsyncClient] = None,
    ):
        self.base_url = (base_url or settings.NOMINATIM_BASE_URL).rstrip("/")
        self.user_agent = user_agent or settings.NOMINATIM_USER_AGENT
        self.timeout = timeout if timeout is not None else settings.NOMINATIM_TIMEOUT_SECONDS
        self._client = client

    def _get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }

    async def _send_request(self, endpoint: str, params: Dict[str, Any]) -> Any:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()

        async def _execute(c: httpx.AsyncClient) -> httpx.Response:
            return await c.get(url, params=params, headers=headers)

        try:
            if self._client is not None:
                response = await _execute(self._client)
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as c:
                    response = await _execute(c)

            if response.status_code == 403:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Dịch vụ bản đồ OpenStreetMap tạm thời từ chối yêu cầu (403). Vui lòng thử lại sau.",
                )
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Dịch vụ OpenStreetMap không phản hồi kịp thời (Timeout).",
            )
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Lỗi khi kết nối với máy chủ OpenStreetMap: {str(exc)}",
            )

    async def search(self, query: str, limit: int = 10) -> MapSearchResponse:
        params = {
            "q": query,
            "format": "jsonv2",
            "limit": limit,
            "addressdetails": 1,
        }
        data = await self._send_request("search", params)

        results: List[PlaceItem] = []
        if isinstance(data, list):
            for item in data:
                try:
                    results.append(
                        PlaceItem(
                            place_id=item.get("place_id"),
                            osm_id=item.get("osm_id"),
                            osm_type=item.get("osm_type"),
                            display_name=item.get("display_name", ""),
                            lat=float(item.get("lat", 0.0)),
                            lon=float(item.get("lon", 0.0)),
                            category=item.get("category"),
                            type=item.get("type"),
                            importance=item.get("importance"),
                            boundingbox=item.get("boundingbox"),
                        )
                    )
                except (ValueError, TypeError):
                    continue

        return MapSearchResponse(
            query=query,
            count=len(results),
            results=results,
        )

    async def reverse(self, lat: float, lon: float) -> MapReverseResponse:
        params = {
            "lat": lat,
            "lon": lon,
            "format": "jsonv2",
            "addressdetails": 1,
        }
        data = await self._send_request("reverse", params)

        if not isinstance(data, dict) or "error" in data:
            error_msg = (
                data.get("error", "Không tìm thấy thông tin địa chỉ tại toạ độ này")
                if isinstance(data, dict)
                else "Không tìm thấy thông tin địa chỉ tại toạ độ này"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        return MapReverseResponse(
            place_id=data.get("place_id"),
            osm_id=data.get("osm_id"),
            osm_type=data.get("osm_type"),
            lat=float(data.get("lat", lat)),
            lon=float(data.get("lon", lon)),
            display_name=data.get("display_name", ""),
            address=data.get("address", {}),
        )


map_service = MapService()
