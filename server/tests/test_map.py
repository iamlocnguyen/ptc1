import json
import httpx
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from server.app.main import app
from server.app.api.v1.endpoints.map import get_map_service
from server.app.services.map_service import MapService


SAMPLE_SEARCH_RESULTS = [
    {
        "place_id": 1001,
        "osm_id": 2001,
        "osm_type": "node",
        "display_name": "Hồ Hoàn Kiếm, Quận Hoàn Kiếm, Hà Nội, Việt Nam",
        "lat": "21.0287",
        "lon": "105.8523",
        "category": "tourism",
        "type": "attraction",
        "importance": 0.85,
        "boundingbox": ["21.02", "21.03", "105.84", "105.86"],
    }
]

SAMPLE_REVERSE_RESULT = {
    "place_id": 1001,
    "osm_id": 2001,
    "osm_type": "node",
    "lat": "21.0287",
    "lon": "105.8523",
    "display_name": "Hồ Hoàn Kiếm, Quận Hoàn Kiếm, Hà Nội, Việt Nam",
    "address": {
        "tourism": "Hồ Hoàn Kiếm",
        "suburb": "Quận Hoàn Kiếm",
        "city": "Hà Nội",
        "country": "Việt Nam",
    },
}


def create_mock_map_service(handler_func) -> MapService:
    transport = httpx.MockTransport(handler_func)
    mock_client = httpx.AsyncClient(transport=transport)
    return MapService(client=mock_client)


def test_map_search_success(client: TestClient):
    """Kiểm tra tìm kiếm địa điểm trả về danh sách địa điểm và toạ độ hợp lệ."""
    def handler(request: httpx.Request) -> httpx.Response:
        assert "search" in str(request.url)
        assert request.headers.get("User-Agent") is not None
        return httpx.Response(200, json=SAMPLE_SEARCH_RESULTS)

    mock_service = create_mock_map_service(handler)
    app.dependency_overrides[get_map_service] = lambda: mock_service

    try:
        response = client.get("/api/v1/map/search", params={"q": "Ho Hoan Kiem", "limit": 5})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["query"] == "Ho Hoan Kiem"
        assert data["count"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["lat"] == 21.0287
        assert data["results"][0]["lon"] == 105.8523
        assert "OpenStreetMap" in data["attribution"]
    finally:
        app.dependency_overrides.pop(get_map_service, None)


def test_map_search_empty_results(client: TestClient):
    """Kiểm tra tìm kiếm không có kết quả trả về count=0 và danh sách rỗng."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    mock_service = create_mock_map_service(handler)
    app.dependency_overrides[get_map_service] = lambda: mock_service

    try:
        response = client.get("/api/v1/map/search", params={"q": "DiaDiemKhongTonTai12345"})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["count"] == 0
        assert data["results"] == []
    finally:
        app.dependency_overrides.pop(get_map_service, None)


def test_map_search_validation_error(client: TestClient):
    """Kiểm tra validation query parameter: thiếu query hoặc limit vượt ngưỡng."""
    # Thiếu param 'q'
    response_missing = client.get("/api/v1/map/search")
    assert response_missing.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Param 'limit' vượt quá giới hạn le=50
    response_invalid_limit = client.get("/api/v1/map/search", params={"q": "Hanoi", "limit": 100})
    assert response_invalid_limit.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_map_reverse_success(client: TestClient):
    """Kiểm tra tra cứu toạ độ ra địa chỉ thành công."""
    def handler(request: httpx.Request) -> httpx.Response:
        assert "reverse" in str(request.url)
        return httpx.Response(200, json=SAMPLE_REVERSE_RESULT)

    mock_service = create_mock_map_service(handler)
    app.dependency_overrides[get_map_service] = lambda: mock_service

    try:
        response = client.get("/api/v1/map/reverse", params={"lat": 21.0287, "lon": 105.8523})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["lat"] == 21.0287
        assert data["lon"] == 105.8523
        assert "Hồ Hoàn Kiếm" in data["display_name"]
        assert data["address"]["city"] == "Hà Nội"
        assert "OpenStreetMap" in data["attribution"]
    finally:
        app.dependency_overrides.pop(get_map_service, None)


def test_map_reverse_not_found(client: TestClient):
    """Kiểm tra toạ độ không tìm thấy địa chỉ trả về 404."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"error": "Unable to geocode"})

    mock_service = create_mock_map_service(handler)
    app.dependency_overrides[get_map_service] = lambda: mock_service

    try:
        response = client.get("/api/v1/map/reverse", params={"lat": 0.0, "lon": 0.0})
        assert response.status_code == status.HTTP_404_NOT_FOUND
    finally:
        app.dependency_overrides.pop(get_map_service, None)


def test_map_reverse_coordinate_validation(client: TestClient):
    """Kiểm tra ràng buộc toạ độ: lat [-90, 90], lon [-180, 180]."""
    # lat ngoài phạm vi
    resp_lat = client.get("/api/v1/map/reverse", params={"lat": 95.0, "lon": 105.0})
    assert resp_lat.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # lon ngoài phạm vi
    resp_lon = client.get("/api/v1/map/reverse", params={"lat": 21.0, "lon": 185.0})
    assert resp_lon.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_map_error_rate_limited_403(client: TestClient):
    """Kiểm tra khi máy chủ OSM trả về 403, server chuyển đổi thành 503 Service Unavailable."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text="Forbidden")

    mock_service = create_mock_map_service(handler)
    app.dependency_overrides[get_map_service] = lambda: mock_service

    try:
        response = client.get("/api/v1/map/search", params={"q": "Hanoi"})
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    finally:
        app.dependency_overrides.pop(get_map_service, None)


def test_map_error_timeout_504(client: TestClient):
    """Kiểm tra khi kết nối OSM bị timeout, server trả về 504 Gateway Timeout."""
    def handler(request: httpx.Request):
        raise httpx.ReadTimeout("Connection timed out", request=request)

    mock_service = create_mock_map_service(handler)
    app.dependency_overrides[get_map_service] = lambda: mock_service

    try:
        response = client.get("/api/v1/map/search", params={"q": "Hanoi"})
        assert response.status_code == status.HTTP_504_GATEWAY_TIMEOUT
    finally:
        app.dependency_overrides.pop(get_map_service, None)


def test_map_error_bad_gateway_502(client: TestClient):
    """Kiểm tra lỗi HTTP chung từ OSM trả về 502 Bad Gateway."""
    def handler(request: httpx.Request):
        raise httpx.ConnectError("Network unreachable", request=request)

    mock_service = create_mock_map_service(handler)
    app.dependency_overrides[get_map_service] = lambda: mock_service

    try:
        response = client.get("/api/v1/map/search", params={"q": "Hanoi"})
        assert response.status_code == status.HTTP_502_BAD_GATEWAY
    finally:
        app.dependency_overrides.pop(get_map_service, None)
