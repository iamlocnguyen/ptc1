from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from server.app.db.session import get_db
from server.app.schemas.restaurant import (
    RestaurantCreate,
    RestaurantUpdate,
    RestaurantResponse,
    NearbyRestaurantResponse,
    DistanceResponse,
)
from server.app.services.restaurant_service import RestaurantService

router = APIRouter()


# ---------------------------------------------------------
# Endpoints dành cho Seller quản lý quán ăn của mình
# ---------------------------------------------------------

@router.post(
    "/sellers/{seller_id}/restaurants",
    response_model=RestaurantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Seller tạo quán ăn mới",
    tags=["Seller Restaurants Management"],
)
def create_restaurant_for_seller(
    seller_id: int,
    payload: RestaurantCreate,
    db: Session = Depends(get_db),
) -> RestaurantResponse:
    """Tạo mới một quán ăn thuộc sở hữu của người bán (Seller)."""
    return RestaurantService.create_restaurant(db=db, seller_id=seller_id, data=payload)


@router.get(
    "/sellers/{seller_id}/restaurants",
    response_model=List[RestaurantResponse],
    summary="Lấy danh sách các quán ăn của Seller",
    tags=["Seller Restaurants Management"],
)
def get_restaurants_for_seller(
    seller_id: int,
    skip: int = Query(0, ge=0, description="Số lượng bản ghi bỏ qua"),
    limit: int = Query(50, ge=1, le=100, description="Số lượng bản ghi tối đa"),
    db: Session = Depends(get_db),
) -> List[RestaurantResponse]:
    """Lấy danh sách toàn bộ quán ăn do Seller này sở hữu."""
    return RestaurantService.get_restaurants_by_seller(
        db=db, seller_id=seller_id, skip=skip, limit=limit
    )


@router.get(
    "/sellers/{seller_id}/restaurants/{restaurant_id}",
    response_model=RestaurantResponse,
    summary="Seller xem chi tiết một quán ăn của mình",
    tags=["Seller Restaurants Management"],
)
def get_single_restaurant_for_seller(
    seller_id: int,
    restaurant_id: int,
    db: Session = Depends(get_db),
) -> RestaurantResponse:
    """Lấy thông tin chi tiết một quán ăn của Seller."""
    restaurant = RestaurantService.get_restaurant_by_id(db=db, restaurant_id=restaurant_id)
    if restaurant.seller_id != seller_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập quán ăn này.",
        )
    return restaurant


@router.put(
    "/sellers/{seller_id}/restaurants/{restaurant_id}",
    response_model=RestaurantResponse,
    summary="Seller cập nhật thông tin quán ăn",
    tags=["Seller Restaurants Management"],
)
def update_restaurant_for_seller(
    seller_id: int,
    restaurant_id: int,
    payload: RestaurantUpdate,
    db: Session = Depends(get_db),
) -> RestaurantResponse:
    """Cập nhật thông tin quán ăn (chỉ người bán sở hữu quán mới có quyền cập nhật)."""
    return RestaurantService.update_restaurant(
        db=db, restaurant_id=restaurant_id, seller_id=seller_id, data=payload
    )


@router.delete(
    "/sellers/{seller_id}/restaurants/{restaurant_id}",
    status_code=status.HTTP_200_OK,
    summary="Seller xoá quán ăn",
    tags=["Seller Restaurants Management"],
)
def delete_restaurant_for_seller(
    seller_id: int,
    restaurant_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """Xoá quán ăn (chỉ người bán sở hữu quán mới có quyền xoá)."""
    RestaurantService.delete_restaurant(
        db=db, restaurant_id=restaurant_id, seller_id=seller_id
    )
    return {"message": "Đã xoá quán ăn thành công.", "restaurant_id": restaurant_id}


# ---------------------------------------------------------
# Endpoints công khai (Public) dành cho Khách hàng & Bản đồ
# ---------------------------------------------------------

@router.get(
    "/restaurants/nearby",
    response_model=List[NearbyRestaurantResponse],
    summary="Khách hàng tìm kiếm các quán ăn xung quanh theo bán kính (PostGIS)",
    tags=["Restaurants (Public)"],
)
def find_nearby_restaurants(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Vĩ độ hiện tại của khách hàng"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Kinh độ hiện tại của khách hàng"),
    radius_km: float = Query(5.0, gt=0, le=100.0, description="Bán kính tìm kiếm (km)"),
    skip: int = Query(0, ge=0, description="Số lượng bản ghi bỏ qua"),
    limit: int = Query(50, ge=1, le=100, description="Số lượng bản ghi tối đa"),
    db: Session = Depends(get_db),
) -> List[NearbyRestaurantResponse]:
    """
    Sử dụng PostGIS (ST_DWithin và ST_Distance trên cột geography) để tìm quán ăn
    trong bán kính radius_km và sắp xếp theo thứ tự từ gần nhất đến xa nhất.
    """
    return RestaurantService.get_nearby_restaurants(
        db=db, lat=lat, lon=lon, radius_km=radius_km, skip=skip, limit=limit
    )


@router.get(
    "/restaurants",
    response_model=List[RestaurantResponse],
    summary="Khách hàng xem danh sách tất cả quán ăn",
    tags=["Restaurants (Public)"],
)
def list_public_restaurants(
    skip: int = Query(0, ge=0, description="Số lượng bản ghi bỏ qua"),
    limit: int = Query(50, ge=1, le=100, description="Số lượng bản ghi tối đa"),
    db: Session = Depends(get_db),
) -> List[RestaurantResponse]:
    """Lấy danh sách các quán ăn đang hoạt động để hiển thị lên bản đồ hoặc danh sách khám phá."""
    return RestaurantService.get_all_active_restaurants(
        db=db, skip=skip, limit=limit, active_only=True
    )


@router.get(
    "/restaurants/{restaurant_id}/distance",
    response_model=DistanceResponse,
    summary="Khách hàng tính khoảng cách từ vị trí của mình đến quán ăn (PostGIS)",
    tags=["Restaurants (Public)"],
)
def get_distance_to_restaurant(
    restaurant_id: int,
    lat: float = Query(..., ge=-90.0, le=90.0, description="Vĩ độ hiện tại của khách hàng"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Kinh độ hiện tại của khách hàng"),
    db: Session = Depends(get_db),
) -> DistanceResponse:
    """Tính khoảng cách chính xác theo mét và km sử dụng hàm PostGIS ST_Distance."""
    return RestaurantService.calculate_distance_to_restaurant(
        db=db, restaurant_id=restaurant_id, lat=lat, lon=lon
    )


@router.get(
    "/restaurants/{restaurant_id}",
    response_model=RestaurantResponse,
    summary="Khách hàng xem chi tiết toạ độ quán ăn để dẫn đường",
    tags=["Restaurants (Public)"],
)
def get_public_restaurant_detail(
    restaurant_id: int,
    db: Session = Depends(get_db),
) -> RestaurantResponse:
    """Lấy thông tin chi tiết của quán ăn gồm toạ độ (latitude, longitude) để thực hiện dẫn đường."""
    return RestaurantService.get_restaurant_by_id(db=db, restaurant_id=restaurant_id)
