from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class UserRegister(BaseModel):
    email: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Địa chỉ email người dùng",
        examples=["user@example.com"],
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=72,
        description="Mật khẩu tài khoản (tối thiểu 6 ký tự)",
        examples=["SecretPass123"],
    )
    full_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Họ và tên đầy đủ",
        examples=["Nguyễn Văn A"],
    )


class UserLogin(BaseModel):
    email: str = Field(
        ...,
        description="Địa chỉ email đăng nhập",
        examples=["user@example.com"],
    )
    password: str = Field(
        ...,
        description="Mật khẩu đăng nhập",
        examples=["SecretPass123"],
    )


class UserResponse(BaseModel):
    id: int = Field(..., description="ID của người dùng", examples=[1])
    email: str = Field(..., description="Địa chỉ email", examples=["user@example.com"])
    full_name: Optional[str] = Field(None, description="Họ và tên")
    is_active: bool = Field(True, description="Trạng thái kích hoạt")
    created_at: datetime = Field(..., description="Thời gian tạo tài khoản")

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    message: str = Field("Login successful", description="Thông báo đăng nhập")
    user: UserResponse = Field(..., description="Thông tin người dùng đã đăng nhập")
