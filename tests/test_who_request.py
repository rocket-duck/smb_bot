from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from bot.config import settings as settings_module
from bot.messages import who_request


@pytest.mark.asyncio
async def test_who_request_sends_only_in_allowed_chat(tmp_path, monkeypatch):
    img_dir = tmp_path / "img"
    img_dir.mkdir()
    (img_dir / "a_kto.jpg").write_bytes(b"fake")

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
    photo = message.answer_photo.await_args.kwargs["photo"]
    assert str(photo.path).endswith("a_kto.jpg")


@pytest.mark.asyncio
async def test_who_request_ignored_outside_allowed_chat(tmp_path, monkeypatch):
    img_dir = tmp_path / "img"
    img_dir.mkdir()
    (img_dir / "a_kto.jpg").write_bytes(b"fake")

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


@pytest.mark.asyncio
async def test_who_request_sends_loh_on_force(tmp_path, monkeypatch):
    img_dir = tmp_path / "img"
    img_dir.mkdir()
    (img_dir / "loh.jpg").write_bytes(b"fake")

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

    await who_request.handle_who_request(
        message,
        who_request_enable=True,
        force_image_name="loh.jpg",
    )

    message.answer_photo.assert_awaited_once()
    photo = message.answer_photo.await_args.kwargs["photo"]
    assert str(photo.path).endswith("loh.jpg")


@pytest.mark.asyncio
async def test_who_request_sends_roll_message(tmp_path, monkeypatch):
    img_dir = tmp_path / "img"
    img_dir.mkdir()
    (img_dir / "a_kto.jpg").write_bytes(b"fake")

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

    await who_request.handle_who_request(
        message,
        who_request_enable=True,
        user_roll=5,
        bot_roll=12,
    )

    message.answer_photo.assert_awaited_once()
    kwargs = message.answer_photo.await_args.kwargs
    assert kwargs["caption"] == "roll 1d20\nUser roll: 5\nBot roll: 12"


@pytest.mark.asyncio
async def test_who_request_sends_bot_one_on_force(tmp_path, monkeypatch):
    img_dir = tmp_path / "img"
    img_dir.mkdir()
    (img_dir / "bot_one.jpg").write_bytes(b"fake")

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

    await who_request.handle_who_request(
        message,
        who_request_enable=True,
        force_image_name="bot_one.jpg",
    )

    message.answer_photo.assert_awaited_once()
    photo = message.answer_photo.await_args.kwargs["photo"]
    assert str(photo.path).endswith("bot_one.jpg")
