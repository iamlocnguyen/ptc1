from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from server.app.models.user import User
from server.app.schemas.user import UserRegister
from server.app.core.security import hash_password, verify_password


class UserService:
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Tìm người dùng theo email (chuẩn hóa về chữ thường)."""
        normalized_email = email.strip().lower()
        statement = select(User).where(User.email == normalized_email)
        return db.scalars(statement).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Lấy thông tin người dùng theo ID."""
        return db.get(User, user_id)

    @staticmethod
    def create_user(db: Session, user_in: UserRegister) -> User:
        """Tạo người dùng mới và mã hóa mật khẩu an toàn."""
        db_user = User(
            email=user_in.email.strip().lower(),
            hashed_password=hash_password(user_in.password),
            full_name=user_in.full_name,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Xác thực người dùng bằng email và mật khẩu."""
        user = UserService.get_user_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
