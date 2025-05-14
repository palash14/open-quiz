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
    ACCESS_TOKEN_EXPIRE_MINUTES: int = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", (60 * 24 * 7))
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    REFRESH_TOKEN_EXPIRE_DAYS: int = os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 30)

    # SMTP server configuration
    SMTP_HOST: str = os.getenv("SMTP_HOST", "mailpit")
    SMTP_PORT: int = os.getenv("SMTP_PORT", 1025)
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_ENCRYPTION: str = os.getenv("SMTP_ENCRYPTION", "")
    SENDER_EMAIL: str = os.getenv("SENDER_EMAIL", "no-reply@example.com")
    MAIL_FROM_NAME: str = os.getenv("MAIL_FROM_NAME", "${PROJECT_NAME}")

    # REDIS
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = os.getenv("REDIS_PORT", 6379)
    REDIS_QUEUE_EMAIL: str = os.getenv("REDIS_QUEUE_EMAIL", "email")

    # Google OAuth settings
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "")
    GOOGLE_AUTHORIZATION_BASE_URL: str = os.getenv("GOOGLE_AUTHORIZATION_BASE_URL", "")
    GOOGLE_TOKEN_URL: str = os.getenv("GOOGLE_TOKEN_URL", "")
    GOOGLE_SCOPE: str = os.getenv("GOOGLE_SCOPE", "")

    # Github OAuth settings
    GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")
    GITHUB_REDIRECT_URI: str = os.getenv("GITHUB_REDIRECT_URI", "")

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
