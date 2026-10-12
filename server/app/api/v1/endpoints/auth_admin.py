from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from server.app.db.session import get_db
from server.app.schemas.admin import AdminLogin
from server.app.schemas.common import RoleLoginResponse
from server.app.services.admin_service import AdminService

router = APIRouter()


@router.post(
    "/login",
    response_model=RoleLoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Đăng nhập tài khoản Admin",
    description="Kiểm tra email và mật khẩu trong bảng admins.",
)
def login_admin(
    admin_in: AdminLogin,
    db: Session = Depends(get_db),
) -> RoleLoginResponse:
    admin = AdminService.authenticate_admin(db=db, email=admin_in.email, password=admin_in.password)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    admin_dict = {
        "id": admin.id,
        "email": admin.email,
        "full_name": admin.full_name,
        "role_level": admin.role_level,
        "is_active": admin.is_active,
        "created_at": admin.created_at.isoformat(),
    }
    return RoleLoginResponse(
        message="Admin login successful",
        role="admin",
        data=admin_dict,
    )
