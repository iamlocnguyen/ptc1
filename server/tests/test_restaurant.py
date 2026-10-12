import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select

from server.app.models.seller import Seller
from server.app.models.restaurant import Restaurant
from server.app.core.security import hash_password


@pytest.fixture
def test_seller(db_session: Session) -> Seller:
    """Fixture tạo một Seller mẫu trong database."""
    seller = Seller(
        email="seller_test@example.com",
        hashed_password=hash_password("seller123"),
        shop_name="Phở Gia Truyền Hà Nội",
        phone="0987654321",
        full_name="Nguyễn Văn Bán",
        is_active=True,
    )
    db_session.add(seller)
    db_session.commit()
    db_session.refresh(seller)
    return seller


@pytest.fixture
def second_seller(db_session: Session) -> Seller:
    """Fixture tạo một Seller thứ hai để kiểm tra bảo mật phân quyền."""
    seller = Seller(
        email="seller_second@example.com",
        hashed_password=hash_password("seller123"),
        shop_name="Bún Chả Hương Liên",
        phone="0912345678",
        full_name="Trần Thị Bán",
        is_active=True,
    )
    db_session.add(seller)
    db_session.commit()
    db_session.refresh(seller)
    return seller


def test_create_restaurant_success(client: TestClient, test_seller: Seller):
    """Kiểm tra Seller tạo quán ăn mới thành công kèm toạ độ bản đồ."""
    payload = {
        "name": "Phở Bát Đàn - Cơ sở 1",
        "address": "49 Bát Đàn, Hoàn Kiếm, Hà Nội",
        "latitude": 21.0335,
        "longitude": 105.8471,
        "phone": "02438255699",
        "description": "Quán phở truyền thống lâu đời",
    }
    response = client.post(f"/api/v1/sellers/{test_seller.id}/restaurants", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["address"] == payload["address"]
    assert data["latitude"] == payload["latitude"]
    assert data["longitude"] == payload["longitude"]
    assert data["seller_id"] == test_seller.id
    assert data["is_active"] is True
    assert "id" in data


def test_one_seller_can_create_multiple_restaurants(client: TestClient, test_seller: Seller):
    """Kiểm tra quan hệ 1 Seller có thể sở hữu nhiều quán ăn."""
    # Tạo quán 1
    client.post(
        f"/api/v1/sellers/{test_seller.id}/restaurants",
        json={
            "name": "Chi nhánh Cầu Giấy",
            "address": "123 Cầu Giấy, Hà Nội",
            "latitude": 21.0360,
            "longitude": 105.7950,
        },
    )
    # Tạo quán 2
    client.post(
        f"/api/v1/sellers/{test_seller.id}/restaurants",
        json={
            "name": "Chi nhánh Đống Đa",
            "address": "456 Xã Đàn, Hà Nội",
            "latitude": 21.0150,
            "longitude": 105.8300,
        },
    )

    # Lấy danh sách quán của Seller
    response = client.get(f"/api/v1/sellers/{test_seller.id}/restaurants")
    assert response.status_code == status.HTTP_200_OK
    items = response.json()
    assert len(items) == 2
    names = [r["name"] for r in items]
    assert "Chi nhánh Cầu Giấy" in names
    assert "Chi nhánh Đống Đa" in names


def test_create_restaurant_nonexistent_seller(client: TestClient):
    """Kiểm tra tạo quán với seller_id không tồn tại trả về 404."""
    payload = {
        "name": "Quán ma",
        "address": "Không rõ",
        "latitude": 21.0,
        "longitude": 105.0,
    }
    response = client.post("/api/v1/sellers/99999/restaurants", json=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_restaurant_success(client: TestClient, test_seller: Seller):
    """Kiểm tra cập nhật thông tin và toạ độ quán ăn thành công."""
    res_create = client.post(
        f"/api/v1/sellers/{test_seller.id}/restaurants",
        json={
            "name": "Quán ban đầu",
            "address": "Địa chỉ cũ",
            "latitude": 21.0,
            "longitude": 105.0,
        },
    )
    res_id = res_create.json()["id"]

    # Cập nhật
    update_payload = {
        "name": "Quán sau khi đổi tên",
        "address": "Địa chỉ mới đẹp hơn",
        "latitude": 21.0285,
        "longitude": 105.8542,
        "phone": "0999999999",
    }
    response = client.put(f"/api/v1/sellers/{test_seller.id}/restaurants/{res_id}", json=update_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Quán sau khi đổi tên"
    assert data["address"] == "Địa chỉ mới đẹp hơn"
    assert data["latitude"] == 21.0285
    assert data["longitude"] == 105.8542
    assert data["phone"] == "0999999999"


def test_update_restaurant_forbidden_by_different_seller(
    client: TestClient, test_seller: Seller, second_seller: Seller
):
    """Kiểm tra Seller B không được phép sửa quán của Seller A (403 Forbidden)."""
    # Seller A tạo quán
    res_create = client.post(
        f"/api/v1/sellers/{test_seller.id}/restaurants",
        json={
            "name": "Quán của Seller A",
            "address": "Hà Nội",
            "latitude": 21.0,
            "longitude": 105.0,
        },
    )
    res_id = res_create.json()["id"]

    # Seller B cố tình sửa quán của Seller A
    response = client.put(
        f"/api/v1/sellers/{second_seller.id}/restaurants/{res_id}",
        json={"name": "Bị Seller B hack tên"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_restaurant_success_and_forbidden(
    client: TestClient, test_seller: Seller, second_seller: Seller
):
    """Kiểm tra xoá quán: Chặn người khác và cho phép chủ sở hữu xoá."""
    # Seller A tạo quán
    res_create = client.post(
        f"/api/v1/sellers/{test_seller.id}/restaurants",
        json={
            "name": "Quán cần xoá",
            "address": "Hà Nội",
            "latitude": 21.0,
            "longitude": 105.0,
        },
    )
    res_id = res_create.json()["id"]

    # Seller B cố xoá -> 403
    resp_forbidden = client.delete(f"/api/v1/sellers/{second_seller.id}/restaurants/{res_id}")
    assert resp_forbidden.status_code == status.HTTP_403_FORBIDDEN

    # Seller A tự xoá -> 200 OK
    resp_delete = client.delete(f"/api/v1/sellers/{test_seller.id}/restaurants/{res_id}")
    assert resp_delete.status_code == status.HTTP_200_OK

    # Lấy lại quán sau khi xoá -> 404 Not Found
    resp_get = client.get(f"/api/v1/sellers/{test_seller.id}/restaurants/{res_id}")
    assert resp_get.status_code == status.HTTP_404_NOT_FOUND


def test_restaurant_coordinate_validation(client: TestClient, test_seller: Seller):
    """Kiểm tra validation toạ độ không hợp lệ: lat ngoài [-90, 90], lon ngoài [-180, 180]."""
    # Latitude > 90
    resp_lat = client.post(
        f"/api/v1/sellers/{test_seller.id}/restaurants",
        json={
            "name": "Quán lỗi lat",
            "address": "Hà Nội",
            "latitude": 95.0,
            "longitude": 105.0,
        },
    )
    assert resp_lat.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Longitude > 180
    resp_lon = client.post(
        f"/api/v1/sellers/{test_seller.id}/restaurants",
        json={
            "name": "Quán lỗi lon",
            "address": "Hà Nội",
            "latitude": 21.0,
            "longitude": 195.0,
        },
    )
    assert resp_lon.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_public_get_restaurants(client: TestClient, test_seller: Seller):
    """Kiểm tra API public cho khách hàng xem danh sách quán và lấy toạ độ dẫn đường."""
    res_create = client.post(
        f"/api/v1/sellers/{test_seller.id}/restaurants",
        json={
            "name": "Cơm Tấm Sài Gòn",
            "address": "789 Nguyễn Trãi, Thanh Xuân, Hà Nội",
            "latitude": 20.9950,
            "longitude": 105.8050,
        },
    )
    res_id = res_create.json()["id"]

    # Public list
    resp_list = client.get("/api/v1/restaurants")
    assert resp_list.status_code == status.HTTP_200_OK
    assert any(r["id"] == res_id for r in resp_list.json())

    # Public detail (dùng toạ độ này để dẫn đường)
    resp_detail = client.get(f"/api/v1/restaurants/{res_id}")
    assert resp_detail.status_code == status.HTTP_200_OK
    assert resp_detail.json()["latitude"] == 20.9950
    assert resp_detail.json()["longitude"] == 105.8050


def test_cascade_delete_seller_deletes_restaurants(db_session: Session):
    """Kiểm tra khi xoá Seller trong DB, toàn bộ quán của Seller đó bị xoá theo (Cascade delete)."""
    seller = Seller(
        email="seller_cascade@example.com",
        hashed_password=hash_password("123456"),
        shop_name="Shop Sắp Xoá",
        is_active=True,
    )
    db_session.add(seller)
    db_session.commit()
    db_session.refresh(seller)

    r1 = Restaurant(
        seller_id=seller.id,
        name="Quán 1",
        address="Đc 1",
        latitude=21.0,
        longitude=105.0,
    )
    r2 = Restaurant(
        seller_id=seller.id,
        name="Quán 2",
        address="Đc 2",
        latitude=21.1,
        longitude=105.1,
    )
    db_session.add_all([r1, r2])
    db_session.commit()

    # Kiểm tra đã có 2 quán
    stmt = select(Restaurant).where(Restaurant.seller_id == seller.id)
    assert len(list(db_session.scalars(stmt).all())) == 2

    # Xoá seller
    db_session.delete(seller)
    db_session.commit()

    # Kiểm tra 2 quán đã tự động bị xoá sạch
    stmt_after = select(Restaurant).where(Restaurant.seller_id == seller.id)
    assert len(list(db_session.scalars(stmt_after).all())) == 0
