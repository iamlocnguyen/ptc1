from fastapi.testclient import TestClient


# ==============================================================================
# 1. USER AUTHENTICATION TESTS (Bảng: users)
# ==============================================================================

def test_register_user_success(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/user/register",
        json={
            "email": "customer@example.com",
            "password": "securepassword123",
            "full_name": "Nguyen Van User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "customer@example.com"
    assert data["full_name"] == "Nguyen Van User"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "password" not in data


def test_register_user_duplicate_email(client: TestClient) -> None:
    payload = {
        "email": "dup_user@example.com",
        "password": "password123",
        "full_name": "User Duplicate",
    }
    resp1 = client.post("/api/v1/auth/user/register", json=payload)
    assert resp1.status_code == 201

    resp2 = client.post("/api/v1/auth/user/register", json=payload)
    assert resp2.status_code == 400
    assert "Email already registered" in resp2.json()["detail"]


def test_login_user_success(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/user/register",
        json={
            "email": "login_user@example.com",
            "password": "MyPassword123",
            "full_name": "Login User",
        },
    )
    response = client.post(
        "/api/v1/auth/user/login",
        json={
            "email": "login_user@example.com",
            "password": "MyPassword123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "user"
    assert data["data"]["email"] == "login_user@example.com"


def test_login_user_wrong_password(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/user/register",
        json={
            "email": "wrong_pwd_user@example.com",
            "password": "CorrectPassword",
        },
    )
    response = client.post(
        "/api/v1/auth/user/login",
        json={
            "email": "wrong_pwd_user@example.com",
            "password": "WrongPassword",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


# ==============================================================================
# 2. SELLER AUTHENTICATION TESTS (Bảng: sellers)
# ==============================================================================

def test_register_seller_success(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/seller/register",
        json={
            "email": "seller@example.com",
            "password": "SellerPassword123",
            "full_name": "Tran Van Seller",
            "shop_name": "Cua Hang Cong Nghe",
            "phone": "0987654321",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "seller@example.com"
    assert data["shop_name"] == "Cua Hang Cong Nghe"
    assert data["phone"] == "0987654321"
    assert "id" in data


def test_register_seller_duplicate_email(client: TestClient) -> None:
    payload = {
        "email": "dup_seller@example.com",
        "password": "password123",
        "shop_name": "Shop A",
    }
    resp1 = client.post("/api/v1/auth/seller/register", json=payload)
    assert resp1.status_code == 201

    resp2 = client.post("/api/v1/auth/seller/register", json=payload)
    assert resp2.status_code == 400
    assert "Email already registered" in resp2.json()["detail"]


def test_login_seller_success(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/seller/register",
        json={
            "email": "login_seller@example.com",
            "password": "SellerPass456",
            "shop_name": "Shop X",
        },
    )
    response = client.post(
        "/api/v1/auth/seller/login",
        json={
            "email": "login_seller@example.com",
            "password": "SellerPass456",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "seller"
    assert data["data"]["shop_name"] == "Shop X"


def test_login_seller_wrong_password(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/seller/login",
        json={
            "email": "nonexistent_seller@example.com",
            "password": "WrongPassword",
        },
    )
    assert response.status_code == 401


# ==============================================================================
# 3. ADMIN AUTHENTICATION TESTS (Bảng: admins)
# ==============================================================================

def test_login_admin_default_success(client: TestClient) -> None:
    """Tài khoản Admin mặc định được tự động seed (admin@example.com / admin123)."""
    response = client.post(
        "/api/v1/auth/admin/login",
        json={
            "email": "admin@example.com",
            "password": "admin123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "admin"
    assert data["data"]["email"] == "admin@example.com"
    assert data["data"]["role_level"] == 1


def test_login_admin_wrong_password(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/admin/login",
        json={
            "email": "admin@example.com",
            "password": "wrong_admin_password",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"
