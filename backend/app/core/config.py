from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# parents[3] points to the Paisalog project root.
ENV_FILE = Path(__file__).resolve().parents[3] / ".env"

class Settings(BaseSettings):
    app_name: str = "PaisaLog API"
    app_version: str = "0.1.0"
    
    database_url: str = Field(..., validation_alias="DATABASE_URL")
    test_database_url: str | None = Field(
        default=None,
        validation_alias="TEST_DATABASE_URL",
    )
    secret_key: str = Field(..., validation_alias="SECRET_KEY")
    
    cookie_secure: bool = Field(
        default=False,
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
    access_token_expire_minutes: int = Field(
        default=1440,
        validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    password_reset_token_expire_minutes: int = Field(
        default=5,
        validation_alias="PASSWORD_RESET_TOKEN_EXPIRE_MINUTES",
    )
    frontend_url: str = Field(
        default="http://localhost:3000",
        validation_alias="FRONTEND_URL",
    )
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()