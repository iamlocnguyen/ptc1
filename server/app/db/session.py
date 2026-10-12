from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from server.app.core.config import settings


def _create_engine():
    """Tạo engine kết nối thuần PostgreSQL qua driver psycopg kèm Connection Pool."""
    return create_engine(
        settings.DATABASE_URL,
        echo=settings.DB_ECHO,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_recycle=1800,
        connect_args={"connect_timeout": 3},
    )


engine = _create_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """Dependency cung cấp database session và đảm bảo giải phóng connection sau request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
