from contextlib import asynccontextmanager
from typing import AsyncGenerator, Generator
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from server.app.main import app
from server.app.db.base import Base
from server.app.db.session import get_db

TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Tạo mới toàn bộ schema bảng cho mỗi test case và dọn dẹp sau khi chạy."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Cung cấp TestClient với get_db dependency đã được override bằng in-memory DB."""
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    @asynccontextmanager
    async def override_lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
        yield

    app.dependency_overrides[get_db] = override_get_db
    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = override_lifespan

    with TestClient(app) as test_client:
        yield test_client

    app.router.lifespan_context = original_lifespan
    app.dependency_overrides.clear()
