from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SellerRegister(BaseModel):
    email: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Địa chỉ email người bán",
        examples=["seller@example.com"],
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=72,
        description="Mật khẩu tài khoản (tối thiểu 6 ký tự)",
        examples=["SellerPass123"],
    )
    full_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Họ và tên chủ cửa hàng",
        examples=["Trần Thị B"],
    )
    shop_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Tên cửa hàng",
        examples=["Shop Công Nghệ ABC"],
    )
    phone: Optional[str] = Field(
        None,
        max_length=50,
        description="Số điện thoại liên hệ",
        examples=["0987654321"],
    )


class SellerLogin(BaseModel):
    email: str = Field(..., description="Email đăng nhập", examples=["seller@example.com"])
    password: str = Field(..., description="Mật khẩu", examples=["SellerPass123"])


class SellerResponse(BaseModel):
    id: int = Field(..., description="ID của người bán", examples=[1])
    email: str = Field(..., description="Địa chỉ email", examples=["seller@example.com"])
    full_name: Optional[str] = Field(None, description="Họ và tên")
    shop_name: str = Field(..., description="Tên cửa hàng", examples=["Shop Công Nghệ ABC"])
    phone: Optional[str] = Field(None, description="Số điện thoại")
    is_active: bool = Field(True, description="Trạng thái kích hoạt")
    created_at: datetime = Field(..., description="Thời gian tạo tài khoản")

    model_config = ConfigDict(from_attributes=True)
