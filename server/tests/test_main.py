from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient) -> None:
    """Kiểm tra root / trả về link tài liệu docs."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["docs"] == "/docs"
    assert data["redoc"] == "/redoc"
