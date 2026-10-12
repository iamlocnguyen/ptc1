from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from server.app.db.base import Base
from server.app.models.base import AccountMixin

if TYPE_CHECKING:
    from server.app.models.restaurant import Restaurant


class Seller(AccountMixin, Base):
    """Bảng người bán hàng (Seller)."""
    __tablename__ = "sellers"

    shop_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default=None)

    restaurants: Mapped[List["Restaurant"]] = relationship(
        "Restaurant",
        back_populates="seller",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
