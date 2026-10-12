from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from server.app.core.security import hash_password, verify_password
from server.app.models.admin import Admin


class AdminService:
    @staticmethod
    def get_admin_by_email(db: Session, email: str) -> Optional[Admin]:
        statement = select(Admin).where(Admin.email == email.strip().lower())
        return db.scalars(statement).first()

    @staticmethod
    def authenticate_admin(db: Session, email: str, password: str) -> Optional[Admin]:
        admin = AdminService.get_admin_by_email(db, email)
        if not admin:
            return None
        if not verify_password(password, admin.hashed_password):
            return None
        return admin

    @staticmethod
    def seed_default_admin(db: Session) -> Admin:
        """Tự động khởi tạo tài khoản Admin mặc định nếu chưa tồn tại trong hệ thống."""
        default_email = "admin@example.com"
        admin = AdminService.get_admin_by_email(db, default_email)
        if not admin:
            admin = Admin(
                email=default_email,
                hashed_password=hash_password("admin123"),
                full_name="System Administrator",
                role_level=1,
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
        return admin
