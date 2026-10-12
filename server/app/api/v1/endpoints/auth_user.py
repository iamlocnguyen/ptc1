from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from server.app.db.session import get_db
from server.app.schemas.user import UserRegister, UserLogin, UserResponse
from server.app.schemas.common import RoleLoginResponse
from server.app.services.user_service import UserService

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản User",
    description="Nhận thông tin đăng ký người dùng thông thường và lưu vào bảng users.",
)
def register_user(
    user_in: UserRegister,
    db: Session = Depends(get_db),
) -> UserResponse:
    existing_user = UserService.get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered for user",
        )
    return UserService.create_user(db=db, user_in=user_in)


@router.post(
    "/login",
    response_model=RoleLoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Đăng nhập tài khoản User",
    description="Kiểm tra email và mật khẩu trong bảng users.",
)
def login_user(
    user_in: UserLogin,
    db: Session = Depends(get_db),
) -> RoleLoginResponse:
    user = UserService.authenticate_user(db=db, email=user_in.email, password=user_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    user_dict = {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat(),
    }
    return RoleLoginResponse(
        message="User login successful",
        role="user",
        data=user_dict,
    )
