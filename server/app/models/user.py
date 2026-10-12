from server.app.db.base import Base
from server.app.models.base import AccountMixin


class User(AccountMixin, Base):
    """Bảng người dùng thông thường (Customer / User)."""
    __tablename__ = "users"
