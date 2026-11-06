from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# parents[3] points to the Paisalog project root.
ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    app_name: str = "PaisaLog API"
    app_version: str = "0.1.0"
    environment: str = Field(
        default="development",
        validation_alias="ENVIRONMENT",
    )

    database_url: str = Field(..., validation_alias="DATABASE_URL")
    test_database_url: str | None = Field(
        default=None,
        validation_alias="TEST_DATABASE_URL",
    )
    secret_key: str = Field(..., validation_alias="SECRET_KEY")

    cookie_secure: bool = Field(
        default=True,
        validation_alias="COOKIE_SECURE",
    )
    cookie_samesite: str = Field(
        default="lax",
        validation_alias="COOKIE_SAMESITE",
    )
    cors_origins: list[str] = Field(
        default_factory=list,
        validation_alias="CORS_ORIGINS",
    )
    db_pool_size: int = Field(default=10, validation_alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, validation_alias="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(default=30, validation_alias="DB_POOL_TIMEOUT")
    db_pool_recycle: int = Field(default=1800, validation_alias="DB_POOL_RECYCLE")
    access_token_expire_minutes: int = Field(
        default=1440,
        validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    password_reset_token_expire_minutes: int = Field(
        default=5,
        validation_alias="PASSWORD_RESET_TOKEN_EXPIRE_MINUTES",
    )
    password_reset_rate_limit_count: int = Field(
        default=3,
        validation_alias="PASSWORD_RESET_RATE_LIMIT_COUNT",
    )
    password_reset_rate_limit_window_minutes: int = Field(
        default=15,
        validation_alias="PASSWORD_RESET_RATE_LIMIT_WINDOW_MINUTES",
    )
    account_reactivation_token_expire_minutes: int = Field(
        default=30,
        validation_alias="ACCOUNT_REACTIVATION_TOKEN_EXPIRE_MINUTES",
    )
    account_reactivation_rate_limit_count: int = Field(
        default=3,
        validation_alias="ACCOUNT_REACTIVATION_RATE_LIMIT_COUNT",
    )
    account_reactivation_rate_limit_window_minutes: int = Field(
        default=15,
        validation_alias="ACCOUNT_REACTIVATION_RATE_LIMIT_WINDOW_MINUTES",
    )
    email_verification_token_expire_minutes: int = Field(
        default=1440,
        validation_alias="EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES",
    )
    email_verification_rate_limit_count: int = Field(
        default=3,
        validation_alias="EMAIL_VERIFICATION_RATE_LIMIT_COUNT",
    )
    email_verification_rate_limit_window_minutes: int = Field(
        default=15,
        validation_alias="EMAIL_VERIFICATION_RATE_LIMIT_WINDOW_MINUTES",
    )
    email_change_token_expire_minutes: int = Field(
        default=60,
        validation_alias="EMAIL_CHANGE_TOKEN_EXPIRE_MINUTES",
    )
    email_change_rate_limit_count: int = Field(
        default=3,
        validation_alias="EMAIL_CHANGE_RATE_LIMIT_COUNT",
    )
    email_change_rate_limit_window_minutes: int = Field(
        default=15,
        validation_alias="EMAIL_CHANGE_RATE_LIMIT_WINDOW_MINUTES",
    )
    frontend_url: str = Field(
        default="http://localhost:3000",
        validation_alias="FRONTEND_URL",
    )
    smtp_host: str = Field(default="localhost", validation_alias="SMTP_HOST")
    smtp_port: int = Field(default=1025, validation_alias="SMTP_PORT")
    smtp_username: str | None = Field(default=None, validation_alias="SMTP_USERNAME")
    smtp_password: str | None = Field(default=None, validation_alias="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=False, validation_alias="SMTP_USE_TLS")
    email_from: str = Field(
        default="noreply@paisalog.local",
        validation_alias="EMAIL_FROM",
    )

    @model_validator(mode="after")
    def validate_cookie_security(self) -> "Settings":
        if self.environment.lower() == "production" and not self.cookie_secure:
            raise ValueError("COOKIE_SECURE must be true in production")
        return self

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
