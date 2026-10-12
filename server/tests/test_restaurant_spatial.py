import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select, text

from server.app.models.seller import Seller
from server.app.models.restaurant import Restaurant
from server.app.core.security import hash_password


@pytest.fixture
def spatial_seller(db_session: Session) -> Seller:
    """Fixture tạo Seller để test không gian PostGIS."""
    seller = Seller(
        email="spatial_seller@example.com",
        hashed_password=hash_password("seller123"),
        shop_name="Chuỗi Quán Ăn Hà Nội",
        is_active=True,
    )
    db_session.add(seller)
    db_session.commit()
    db_session.refresh(seller)
    return seller


def test_postgis_location_column_automatically_populated(
    db_session: Session, spatial_seller: Seller
):
    """Kiểm tra cột PostGIS 'location' được PostgreSQL tự động sinh từ lat/lon (Generated Column)."""
    restaurant = Restaurant(
        seller_id=spatial_seller.id,
        name="Phở Bát Đàn",
        address="49 Bát Đàn, Hà Nội",
        latitude=21.0335,
        longitude=105.8471,
    )
    db_session.add(restaurant)
    db_session.commit()
    db_session.refresh(restaurant)

    # Truy vấn PostGIS kiểm tra toạ độ geometry qua ST_AsText
    stmt = text("SELECT ST_AsText(location) FROM restaurants WHERE id = :id")
    point_text = db_session.execute(stmt, {"id": restaurant.id}).scalar()
    assert point_text is not None
    assert point_text.startswith("POINT(105.8471 21.0335)")


def test_find_nearby_restaurants_within_radius(
    client: TestClient, spatial_seller: Seller
):
    """
    Kiểm tra tìm kiếm quán ăn xung quanh vị trí khách hàng:
    - Vị trí khách: Hồ Hoàn Kiếm (lat: 21.0287, lon: 105.8523)
    - Quán 1: Phở Bát Đàn (cách ~760m)
    - Quán 2: Bún Chả Lê Văn Hưu (cách ~1.6km)
    - Quán 3: Bánh Đa Cua Hải Phòng (cách ~90km)
    Khi tìm bán kính 3km -> Chỉ ra Quán 1 & Quán 2, sắp xếp từ gần đến xa.
    """
    # Tạo 3 quán
    client.post(
        f"/api/v1/sellers/{spatial_seller.id}/restaurants",
        json={
            "name": "Phở Bát Đàn",
            "address": "49 Bát Đàn, Hoàn Kiếm, Hà Nội",
            "latitude": 21.0335,
            "longitude": 105.8471,
        },
    )
    client.post(
        f"/api/v1/sellers/{spatial_seller.id}/restaurants",
        json={
            "name": "Bún Chả Hương Liên",
            "address": "24 Lê Văn Hưu, Hai Bà Trưng, Hà Nội",
            "latitude": 21.0145,
            "longitude": 105.8525,
        },
    )
    client.post(
        f"/api/v1/sellers/{spatial_seller.id}/restaurants",
        json={
            "name": "Bánh Đa Cua Bể Hải Phòng",
            "address": "Trần Phú, Ngô Quyền, Hải Phòng",
            "latitude": 20.8449,
            "longitude": 106.6881,
        },
    )

    # Khách đứng ở Hồ Hoàn Kiếm, tìm quán trong bán kính 3.0 km
    response = client.get(
        "/api/v1/restaurants/nearby",
        params={
            "lat": 21.0287,
            "lon": 105.8523,
            "radius_km": 3.0,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    items = response.json()

    # Chỉ có 2 quán tại Hà Nội nằm trong bán kính 3km
    assert len(items) == 2

    # Quán gần hơn phải đứng trước
    assert items[0]["name"] == "Phở Bát Đàn"
    assert items[0]["distance_km"] < 1.0
    assert items[0]["distance_meters"] < 1000

    assert items[1]["name"] == "Bún Chả Hương Liên"
    assert items[1]["distance_km"] > items[0]["distance_km"]


def test_find_nearby_restaurants_empty_when_out_of_range(client: TestClient):
    """Kiểm tra khi không có quán nào trong bán kính tìm kiếm -> trả về danh sách rỗng."""
    response = client.get(
        "/api/v1/restaurants/nearby",
        params={
            "lat": 8.6000,
            "lon": 104.7000,
            "radius_km": 5.0,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_calculate_distance_to_specific_restaurant(
    client: TestClient, spatial_seller: Seller
):
    """Kiểm tra tính khoảng cách từ toạ độ người dùng đến một quán ăn cụ thể."""
    res_create = client.post(
        f"/api/v1/sellers/{spatial_seller.id}/restaurants",
        json={
            "name": "Phở Bát Đàn",
            "address": "49 Bát Đàn, Hoàn Kiếm, Hà Nội",
            "latitude": 21.0335,
            "longitude": 105.8471,
        },
    )
    res_id = res_create.json()["id"]

    # Người dùng từ Hồ Gươm tính khoảng cách tới quán
    response = client.get(
        f"/api/v1/restaurants/{res_id}/distance",
        params={
            "lat": 21.0287,
            "lon": 105.8523,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["restaurant_id"] == res_id
    assert data["restaurant_name"] == "Phở Bát Đàn"
    # Khoảng cách khoảng 758 mét (~0.76 km)
    assert 700 <= data["distance_meters"] <= 800
    assert 0.70 <= data["distance_km"] <= 0.85
