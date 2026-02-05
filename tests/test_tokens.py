import pytest

from bot.config.settings import get_settings


@pytest.mark.parametrize("missing", ["BOT_USERNAME", "API_TOKEN", "OPENAI_API_KEY"])
def test_missing_env_var_raises(monkeypatch, missing):
    monkeypatch.setenv("BOT_USERNAME", "test-bot")
    monkeypatch.setenv("API_TOKEN", "test-token")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai")
    monkeypatch.delenv(missing, raising=False)
    with pytest.raises(RuntimeError) as excinfo:
        get_settings.cache_clear()
        get_settings()
    assert missing in str(excinfo.value)

    monkeypatch.setenv(missing, "restored")
    get_settings.cache_clear()
    assert get_settings()
