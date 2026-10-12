from fastapi.testclient import TestClient


def test_swagger_ui_page_loads(client: TestClient) -> None:
    """Kiểm tra trang Swagger UI (/docs) tải thành công mã 200 và chứa Swagger UI HTML."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower()


def test_redoc_page_loads(client: TestClient) -> None:
    """Kiểm tra trang ReDoc (/redoc) tải thành công mã 200."""
    response = client.get("/redoc")
    assert response.status_code == 200
    assert "redoc" in response.text.lower()


def test_openapi_json_schema(client: TestClient) -> None:
    """Kiểm tra endpoint /openapi.json trả về schema OpenAPI hợp lệ cho 3 role bảng (User, Seller, Admin)."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "paths" in schema

    # Kiểm tra endpoints của 3 role
    paths = schema["paths"]
    assert "/api/v1/auth/user/register" in paths
    assert "/api/v1/auth/user/login" in paths
    assert "/api/v1/auth/seller/register" in paths
    assert "/api/v1/auth/seller/login" in paths
    assert "/api/v1/auth/admin/login" in paths

    # Khẳng định không còn route guest, items hay health
    assert "/api/v1/health" not in paths
    assert not any("/guest" in p for p in paths)
    assert not any("/items" in p for p in paths)

    # Kiểm tra components schemas của 3 role
    schemas = schema["components"]["schemas"]
    assert "UserRegister" in schemas
    assert "SellerRegister" in schemas
    assert "AdminLogin" in schemas
    assert not any("Guest" in name for name in schemas)

    # Kiểm tra tags của 3 role
    tag_names = [tag["name"] for tag in schema.get("tags", [])]
    assert "User Authentication" in tag_names
    assert "Seller Authentication" in tag_names
    assert "Admin Authentication" in tag_names
    assert "Guest Session" not in tag_names
    assert "Health Check" not in tag_names
    assert "Items Management" not in tag_names
