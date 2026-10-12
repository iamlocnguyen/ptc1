from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from server.app.core.security import hash_password, verify_password
from server.app.models.seller import Seller
from server.app.schemas.seller import SellerRegister


class SellerService:
    @staticmethod
    def get_seller_by_email(db: Session, email: str) -> Optional[Seller]:
        statement = select(Seller).where(Seller.email == email.strip().lower())
        return db.scalars(statement).first()

    @staticmethod
    def create_seller(db: Session, seller_in: SellerRegister) -> Seller:
        db_seller = Seller(
            email=seller_in.email.strip().lower(),
            hashed_password=hash_password(seller_in.password),
            full_name=seller_in.full_name,
            shop_name=seller_in.shop_name,
            phone=seller_in.phone,
        )
        db.add(db_seller)
        db.commit()
        db.refresh(db_seller)
        return db_seller

    @staticmethod
    def authenticate_seller(db: Session, email: str, password: str) -> Optional[Seller]:
        seller = SellerService.get_seller_by_email(db, email)
        if not seller:
            return None
        if not verify_password(password, seller.hashed_password):
            return None
        return seller
