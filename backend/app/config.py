from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "EduSight Africa API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"
    DEBUG: bool = True
    SEED_DEMO_DATA: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/edusight_africa"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 300  # 5 minutes default

    # JWT
    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string-at-least-32-chars"
    REFRESH_SECRET_KEY: str = "change-me-refresh-secret-use-a-long-random-string-at-least-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    ALLOWED_ORIGINS: list[str] = ["*"]
    PARTNER_API_KEYS: str = ""

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # ML serving
    ML_MODEL_PATH: str = "ml/models/xgb_model.pkl"
    ML_SCALER_PATH: str = "ml/models/scaler.pkl"
    ML_METADATA_PATH: str = "ml/models/model_metadata.json"
    ML_ENABLE_TRAINED_MODEL: bool = False
    ML_MIN_CONFIDENCE: float = 0.45
    ML_HIGH_RECALL_MODE: bool = True

    @property
    def partner_api_key_list(self) -> list[str]:
        return [item.strip() for item in self.PARTNER_API_KEYS.split(",") if item.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
