import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_cookie_security_defaults_to_secure(monkeypatch):
    monkeypatch.delenv("COOKIE_SECURE", raising=False)
    settings = Settings(
        DATABASE_URL="postgresql://localhost/paisalog",
        SECRET_KEY="test-secret",
        _env_file=None,
    )

    assert settings.cookie_secure is True


def test_production_rejects_insecure_cookies():
    with pytest.raises(ValidationError, match="COOKIE_SECURE must be true"):
        Settings(
            DATABASE_URL="postgresql://localhost/paisalog",
            SECRET_KEY="test-secret",
            ENVIRONMENT="production",
            COOKIE_SECURE=False,
            _env_file=None,
        )
