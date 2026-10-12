from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select, func, literal, Float
from sqlalchemy.orm import Session
from geoalchemy2 import Geography

from server.app.models.seller import Seller
from server.app.models.restaurant import Restaurant
from server.app.schemas.restaurant import RestaurantCreate, RestaurantUpdate


class RestaurantService:
    @staticmethod
    def create_restaurant(
        db: Session,
        seller_id: int,
        data: RestaurantCreate,
    ) -> Restaurant:
        """Tạo một quán ăn mới thuộc sở hữu của Seller."""
        seller = db.get(Seller, seller_id)
        if not seller:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy người bán (Seller) với ID {seller_id}.",
            )

        restaurant = Restaurant(
            seller_id=seller_id,
            name=data.name.strip(),
            address=data.address.strip(),
            latitude=data.latitude,
            longitude=data.longitude,
            phone=data.phone.strip() if data.phone else None,
            description=data.description.strip() if data.description else None,
            is_active=True,
        )
        db.add(restaurant)
        db.commit()
        db.refresh(restaurant)
        return restaurant

    @staticmethod
    def get_restaurants_by_seller(
        db: Session,
        seller_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Restaurant]:
        """Lấy danh sách tất cả quán ăn do Seller quản lý."""
        seller = db.get(Seller, seller_id)
        if not seller:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy người bán (Seller) với ID {seller_id}.",
            )

        stmt = (
            select(Restaurant)
            .where(Restaurant.seller_id == seller_id)
            .order_by(Restaurant.id.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_restaurant_by_id(
        db: Session,
        restaurant_id: int,
    ) -> Restaurant:
        """Lấy thông tin chi tiết của 1 quán ăn theo ID."""
        restaurant = db.get(Restaurant, restaurant_id)
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy quán ăn với ID {restaurant_id}.",
            )
        return restaurant

    @staticmethod
    def update_restaurant(
        db: Session,
        restaurant_id: int,
        seller_id: int,
        data: RestaurantUpdate,
    ) -> Restaurant:
        """Cập nhật thông tin quán ăn, kiểm tra chặt chẽ quyền sở hữu của Seller."""
        restaurant = db.get(Restaurant, restaurant_id)
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy quán ăn với ID {restaurant_id}.",
            )

        if restaurant.seller_id != seller_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền chỉnh sửa quán ăn của người bán khác.",
            )

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if isinstance(value, str):
                value = value.strip()
            setattr(restaurant, key, value)

        db.commit()
        db.refresh(restaurant)
        return restaurant

    @staticmethod
    def delete_restaurant(
        db: Session,
        restaurant_id: int,
        seller_id: int,
    ) -> bool:
        """Xoá một quán ăn, kiểm tra chặt chẽ quyền sở hữu của Seller."""
        restaurant = db.get(Restaurant, restaurant_id)
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy quán ăn với ID {restaurant_id}.",
            )

        if restaurant.seller_id != seller_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền xoá quán ăn của người bán khác.",
            )

        db.delete(restaurant)
        db.commit()
        return True

    @staticmethod
    def get_all_active_restaurants(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
    ) -> List[Restaurant]:
        """Lấy danh sách các quán ăn công khai cho khách hàng và bản đồ."""
        stmt = select(Restaurant).order_by(Restaurant.id.desc()).offset(skip)
        if active_only:
            stmt = stmt.where(Restaurant.is_active.is_(True))
        stmt = stmt.limit(limit)
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_nearby_restaurants(
        db: Session,
        lat: float,
        lon: float,
        radius_km: float = 5.0,
        skip: int = 0,
        limit: int = 50,
        active_only: bool = True,
    ) -> List[dict]:
        """
        Tìm kiếm các quán ăn trong bán kính radius_km sử dụng hàm PostGIS ST_DWithin.
        Tự động tính khoảng cách thực tế (mét và km) và sắp xếp từ gần đến xa qua ST_Distance.
        """
        user_point = func.ST_SetSRID(func.ST_MakePoint(literal(lon, Float), literal(lat, Float)), 4326).cast(Geography)
        distance_meters_expr = func.ST_Distance(Restaurant.location, user_point).label("distance_meters")

        stmt = select(
            Restaurant,
            distance_meters_expr,
        ).where(
            func.ST_DWithin(Restaurant.location, user_point, radius_km * 1000.0)
        )

        if active_only:
            stmt = stmt.where(Restaurant.is_active.is_(True))

        stmt = stmt.order_by(distance_meters_expr.asc()).offset(skip).limit(limit)

        results = []
        for restaurant, dist_m in db.execute(stmt).all():
            data = {
                "id": restaurant.id,
                "seller_id": restaurant.seller_id,
                "name": restaurant.name,
                "address": restaurant.address,
                "latitude": restaurant.latitude,
                "longitude": restaurant.longitude,
                "phone": restaurant.phone,
                "description": restaurant.description,
                "is_active": restaurant.is_active,
                "created_at": restaurant.created_at,
                "distance_meters": round(float(dist_m), 1),
                "distance_km": round(float(dist_m) / 1000.0, 2),
            }
            results.append(data)
        return results

    @staticmethod
    def calculate_distance_to_restaurant(
        db: Session,
        restaurant_id: int,
        lat: float,
        lon: float,
    ) -> dict:
        """Tính khoảng cách từ toạ độ người dùng đến quán ăn cụ thể sử dụng PostGIS."""
        restaurant = RestaurantService.get_restaurant_by_id(db=db, restaurant_id=restaurant_id)
        user_point = func.ST_SetSRID(func.ST_MakePoint(literal(lon, Float), literal(lat, Float)), 4326).cast(Geography)
        stmt = select(func.ST_Distance(Restaurant.location, user_point)).where(Restaurant.id == restaurant_id)
        dist_m = db.scalar(stmt)
        if dist_m is None:
            dist_m = 0.0
        return {
            "restaurant_id": restaurant_id,
            "restaurant_name": restaurant.name,
            "distance_meters": round(float(dist_m), 1),
            "distance_km": round(float(dist_m) / 1000.0, 2),
        }
