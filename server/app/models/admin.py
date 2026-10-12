from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column
from server.app.db.base import Base
from server.app.models.base import AccountMixin


class Admin(AccountMixin, Base):
    """Bảng quản trị viên hệ thống (Admin)."""
    __tablename__ = "admins"

    role_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
