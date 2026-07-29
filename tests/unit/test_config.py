import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_load_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_NAME", "Test SupportIQ")
    monkeypatch.setenv("ENVIRONMENT", "test")

    settings = Settings()

    assert settings.app_name == "Test SupportIQ"
    assert settings.environment == "test"


def test_settings_reject_unknown_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "unknown")

    with pytest.raises(ValidationError):
        Settings()
