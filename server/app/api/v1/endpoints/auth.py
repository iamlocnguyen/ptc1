from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from server.app.db.session import get_db
from server.app.schemas.user import UserRegister, UserLogin, UserResponse, LoginResponse
from server.app.services.user_service import UserService

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản người dùng mới",
    description="Nhận thông tin đăng ký, băm mật khẩu an toàn và lưu vào cơ sở dữ liệu.",
)
def register(
    user_in: UserRegister,
    db: Session = Depends(get_db),
) -> UserResponse:
    existing_user = UserService.get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    return UserService.create_user(db=db, user_in=user_in)


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Đăng nhập tài khoản",
    description="Kiểm tra email và mật khẩu. Trả về thông tin người dùng nếu hợp lệ.",
)
def login(
    user_in: UserLogin,
    db: Session = Depends(get_db),
) -> LoginResponse:
    user = UserService.authenticate_user(db=db, email=user_in.email, password=user_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return LoginResponse(
        message="Login successful",
        user=user,
    )
