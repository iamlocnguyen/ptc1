from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "PTC1 FastAPI Server"
    APP_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["*"]

    DATABASE_URL: str = "postgresql+psycopg://postgres:2005@localhost:5432/ptc1_db"
    TEST_DATABASE_URL: Optional[str] = "postgresql+psycopg://postgres:2005@localhost:5432/ptc1_test_db"
    DB_ECHO: bool = False

    # OpenStreetMap (Nominatim) Settings
    NOMINATIM_BASE_URL: str = "https://nominatim.openstreetmap.org"
    NOMINATIM_USER_AGENT: str = "PTC1-FastAPI-Server/0.1.0 (contact@example.com)"
    NOMINATIM_TIMEOUT_SECONDS: float = 8.0


settings = Settings()
