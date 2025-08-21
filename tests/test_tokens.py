import importlib
import pytest


@pytest.mark.parametrize(
    "missing", ["BOT_USERNAME", "API_TOKEN", "OPENAI_API_KEY"]
)
def test_missing_env_var_raises(monkeypatch, missing):
    import bot.config.tokens as tokens

    monkeypatch.delenv(missing, raising=False)
    with pytest.raises(RuntimeError) as excinfo:
        importlib.reload(tokens)
    assert missing in str(excinfo.value)

    monkeypatch.setenv(missing, "restored")
    importlib.reload(tokens)
