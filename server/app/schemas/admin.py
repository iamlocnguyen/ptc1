from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class AdminLogin(BaseModel):
    email: str = Field(..., description="Email quản trị viên", examples=["admin@example.com"])
    password: str = Field(..., description="Mật khẩu", examples=["admin123"])


class AdminResponse(BaseModel):
    id: int = Field(..., description="ID của quản trị viên", examples=[1])
    email: str = Field(..., description="Địa chỉ email", examples=["admin@example.com"])
    full_name: Optional[str] = Field(None, description="Họ và tên")
    role_level: int = Field(1, description="Cấp bậc quản trị (1: Super Admin)")
    is_active: bool = Field(True, description="Trạng thái kích hoạt")
    created_at: datetime = Field(..., description="Thời gian tạo tài khoản")

    model_config = ConfigDict(from_attributes=True)
