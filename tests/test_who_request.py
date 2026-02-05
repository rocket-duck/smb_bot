from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from bot.config import settings as settings_module
from bot.messages import who_request


@pytest.mark.asyncio
async def test_who_request_sends_only_in_allowed_chat(tmp_path, monkeypatch):
    img_dir = tmp_path / "img"
    img_dir.mkdir()
    (img_dir / "a_kto_cenz.png").write_bytes(b"fake")

    monkeypatch.setattr(who_request, "IMG_DIR", img_dir)
    monkeypatch.setenv("BOT_USERNAME", "test-bot")
    monkeypatch.setenv("API_TOKEN", "test-token")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai")
    monkeypatch.setenv("NFSW_CHAT_ID", "123")
    settings_module.get_settings.cache_clear()

    message = SimpleNamespace(
        text="а кто",
        chat=SimpleNamespace(id=123),
        message_id=1,
        answer_photo=AsyncMock(),
    )

    await who_request.handle_who_request(message, who_request_enable=True)

    message.answer_photo.assert_awaited_once()


@pytest.mark.asyncio
async def test_who_request_ignored_outside_allowed_chat(tmp_path, monkeypatch):
    img_dir = tmp_path / "img"
    img_dir.mkdir()
    (img_dir / "a_kto_cenz.png").write_bytes(b"fake")

    monkeypatch.setattr(who_request, "IMG_DIR", img_dir)
    monkeypatch.setenv("BOT_USERNAME", "test-bot")
    monkeypatch.setenv("API_TOKEN", "test-token")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai")
    monkeypatch.setenv("NFSW_CHAT_ID", "123")
    settings_module.get_settings.cache_clear()

    message = SimpleNamespace(
        text="а кто",
        chat=SimpleNamespace(id=999),
        message_id=1,
        answer_photo=AsyncMock(),
    )

    await who_request.handle_who_request(message, who_request_enable=True)

    message.answer_photo.assert_not_awaited()
