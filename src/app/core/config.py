# src/app/core/config.py
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, validator
from typing import Optional, List, Dict, Any
import os


class Settings(BaseSettings):
    # Application Configuration
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Quiz API")
    PROJECT_DESC: str = os.getenv(
        "PROJECT_DESC", "An API for managing quizzes and users"
    )
    VERSION: str = os.getenv("VERSION", "1.0.0")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev")  # dev, prod, test
    DEBUG: bool = os.getenv("DEBUG", False)
    LOG_DIR_PATH: str = os.getenv("LOG_DIR_PATH", "/app/logs/")

    # Database Configuration
    DATABASE_URI: Optional[PostgresDsn] = os.getenv("DATABASE_URI", None)
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_PRE_PING: bool = True
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # Security Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "secret_key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    JWT_ALGORITHM: str = "HS256"

    # CORS Configuration
    CORS_ALLOW_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True

    @validator("CORS_ALLOW_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Test Configuration
    TEST_DB_NAME: Optional[str] = "test_quiz_db"

    # Documentation Configuration (Swagger/Redoc)
    DOCS_URL: Optional[str] = "/docs"
    REDOC_URL: Optional[str] = "/redoc"

    @validator("DOCS_URL", "REDOC_URL", pre=True)
    def disable_docs_in_production(cls, v: str, values: Dict[str, Any]) -> str:
        if values.get("ENVIRONMENT") == "prod":
            return None
        return v

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
