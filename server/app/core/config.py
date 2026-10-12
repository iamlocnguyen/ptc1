from typing import List
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
    
    DATABASE_URL: str = "sqlite:///./app.db"
    DB_ECHO: bool = False


settings = Settings()
