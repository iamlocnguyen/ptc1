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
    """Kiểm tra endpoint /openapi.json trả về schema OpenAPI hợp lệ."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "paths" in schema
    assert "/api/v1/auth/register" in schema["paths"]
    assert "/api/v1/auth/login" in schema["paths"]
    # Kiểm tra khẳng định không còn bất kỳ endpoint nào liên quan đến health hay items
    assert "/api/v1/health" not in schema["paths"]
    assert not any("/items" in p for p in schema["paths"])

    # Kiểm tra components schemas
    schemas = schema["components"]["schemas"]
    assert "UserRegister" in schemas
    assert "UserLogin" in schemas
    assert "UserResponse" in schemas
    assert not any(name.startswith("Item") for name in schemas)

    # Kiểm tra tags không còn tag Health Check và Items Management
    tag_names = [tag["name"] for tag in schema.get("tags", [])]
    assert "Health Check" not in tag_names
    assert "Items Management" not in tag_names
