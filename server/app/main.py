import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text
from server.app.core.config import settings
from server.app.db.base import Base
from server.app.db.session import engine, SessionLocal
from server.app.api.v1.router import api_router
from server.app.services.admin_service import AdminService
# Import models để Base.metadata nhận diện các bảng trước khi create_all
import server.app.models  # noqa: F401

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Khởi tạo vòng đời ứng dụng: tự động tạo bảng PostgreSQL và seed admin mặc định."""
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        Base.metadata.create_all(bind=engine)
        # Tự động seed tài khoản Admin mặc định
        with SessionLocal() as db:
            AdminService.seed_default_admin(db)
        logger.info("Khởi tạo PostgreSQL tables và seed admin thành công.")
    except Exception as exc:
        logger.warning("Không thể tự động tạo bảng DB khi khởi động: %s", exc)
    yield


openapi_tags = [
    {
        "name": "User Authentication",
        "description": "API đăng ký và đăng nhập dành cho khách hàng / người dùng thông thường.",
    },
    {
        "name": "Seller Authentication",
        "description": "API đăng ký và đăng nhập dành cho người bán hàng (quản lý shop, thông tin liên hệ).",
    },
    {
        "name": "Admin Authentication",
        "description": "API đăng nhập dành cho quản trị viên hệ thống (mặc định: admin@example.com / admin123).",
    },
]


def create_app() -> FastAPI:
    """Khởi tạo FastAPI app với giao diện Swagger UI tương tác."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "### Mẫu FastAPI Backend Template\n\n"
            "- **Cơ sở dữ liệu:** PostgreSQL 14 (qua SQLAlchemy 2.0 & Psycopg 3 driver)\n"
            "- **Phân quyền theo bảng riêng biệt:** Users, Sellers, Admins\n"
            "- **Swagger UI:** Bấm nút **'Try it out'** ở bất kỳ API nào bên dưới để test trực tiếp!\n"
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_tags=openapi_tags,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/", include_in_schema=False)
    def root():
        return {
            "message": f"Chào mừng bạn đến với {settings.APP_NAME}",
            "docs": "/docs",
            "swagger_docs": "/docs",
            "redoc": "/redoc",
        }

    return app


app = create_app()
