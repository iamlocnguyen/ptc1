from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class RestaurantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Tên quán ăn")
    address: str = Field(..., min_length=1, max_length=500, description="Địa chỉ cụ thể của quán ăn")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Vĩ độ (-90 đến 90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Kinh độ (-180 đến 180)")
    phone: Optional[str] = Field(None, max_length=50, description="Số điện thoại quán")
    description: Optional[str] = Field(None, max_length=1000, description="Mô tả quán ăn")


class RestaurantCreate(RestaurantBase):
    pass


class RestaurantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Tên quán ăn")
    address: Optional[str] = Field(None, min_length=1, max_length=500, description="Địa chỉ quán ăn")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Vĩ độ (-90 đến 90)")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Kinh độ (-180 đến 180)")
    phone: Optional[str] = Field(None, max_length=50, description="Số điện thoại quán")
    description: Optional[str] = Field(None, max_length=1000, description="Mô tả quán ăn")
    is_active: Optional[bool] = Field(None, description="Trạng thái hoạt động")


class RestaurantResponse(RestaurantBase):
    id: int
    seller_id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NearbyRestaurantResponse(RestaurantResponse):
    distance_km: float = Field(..., description="Khoảng cách từ người dùng đến quán (km)")
    distance_meters: float = Field(..., description="Khoảng cách từ người dùng đến quán (mét)")


class DistanceResponse(BaseModel):
    restaurant_id: int
    restaurant_name: str
    distance_km: float = Field(..., description="Khoảng cách (km)")
    distance_meters: float = Field(..., description="Khoảng cách (mét)")
