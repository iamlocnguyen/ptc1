from typing import Any, Dict
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(..., description="Email đăng nhập", examples=["user@example.com"])
    password: str = Field(..., description="Mật khẩu", examples=["SecretPass123"])


class RoleLoginResponse(BaseModel):
    message: str = Field("Login successful", description="Thông báo đăng nhập")
    role: str = Field(..., description="Vai trò tài khoản (user, seller, admin)")
    data: Dict[str, Any] = Field(..., description="Thông tin chi tiết của tài khoản đã đăng nhập")
