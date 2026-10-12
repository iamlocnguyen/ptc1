from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from server.app.models.user import User


def test_register_user_success(client: TestClient, db_session: Session):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "securepassword123",
            "full_name": "Nguyen Van A",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Nguyen Van A"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "hashed_password" not in data
    assert "password" not in data

    # Kiểm tra trong DB mật khẩu được băm an toàn
    user = db_session.query(User).filter_by(email="test@example.com").first()
    assert user is not None
    assert user.hashed_password != "securepassword123"
    assert "$" in user.hashed_password


def test_register_duplicate_email(client: TestClient):
    payload = {
        "email": "duplicate@example.com",
        "password": "password123",
        "full_name": "User One",
    }
    # Lần 1: thành công
    resp1 = client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == 201

    # Lần 2: thất bại vì trùng email
    resp2 = client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == 400
    assert resp2.json()["detail"] == "Email already registered"


def test_register_validation_error(client: TestClient):
    # Mật khẩu quá ngắn (< 6 ký tự)
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "short@example.com",
            "password": "123",
        },
    )
    assert response.status_code == 422


def test_login_success(client: TestClient):
    # Đăng ký tài khoản trước
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "login_user@example.com",
            "password": "MyPassword456",
            "full_name": "Login User",
        },
    )

    # Đăng nhập đúng thông tin
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "login_user@example.com",
            "password": "MyPassword456",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Login successful"
    assert data["user"]["email"] == "login_user@example.com"
    assert data["user"]["full_name"] == "Login User"


def test_login_wrong_password(client: TestClient):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "user_wrong_pw@example.com",
            "password": "CorrectPassword",
        },
    )

    # Thử đăng nhập với mật khẩu sai
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "user_wrong_pw@example.com",
            "password": "WrongPassword",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_login_nonexistent_email(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "AnyPassword",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"
