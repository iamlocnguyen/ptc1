from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from server.app.db.session import get_db
from server.app.schemas.seller import SellerRegister, SellerLogin, SellerResponse
from server.app.schemas.common import RoleLoginResponse
from server.app.services.seller_service import SellerService

router = APIRouter()


@router.post(
    "/register",
    response_model=SellerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản Seller",
    description="Nhận thông tin đăng ký người bán hàng và lưu vào bảng sellers.",
)
def register_seller(
    seller_in: SellerRegister,
    db: Session = Depends(get_db),
) -> SellerResponse:
    existing_seller = SellerService.get_seller_by_email(db, seller_in.email)
    if existing_seller:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered for seller",
        )
    return SellerService.create_seller(db=db, seller_in=seller_in)


@router.post(
    "/login",
    response_model=RoleLoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Đăng nhập tài khoản Seller",
    description="Kiểm tra email và mật khẩu trong bảng sellers.",
)
def login_seller(
    seller_in: SellerLogin,
    db: Session = Depends(get_db),
) -> RoleLoginResponse:
    seller = SellerService.authenticate_seller(db=db, email=seller_in.email, password=seller_in.password)
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    seller_dict = {
        "id": seller.id,
        "email": seller.email,
        "full_name": seller.full_name,
        "shop_name": seller.shop_name,
        "phone": seller.phone,
        "is_active": seller.is_active,
        "created_at": seller.created_at.isoformat(),
    }
    return RoleLoginResponse(
        message="Seller login successful",
        role="seller",
        data=seller_dict,
    )
