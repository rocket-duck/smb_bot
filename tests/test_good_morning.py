import os
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from bot.utils import good_morning


@pytest.mark.asyncio
async def test_send_good_morning_no_chat_id(monkeypatch):
    bot = AsyncMock()
    monkeypatch.setattr(good_morning, "GOOD_MORNING_CHAT_ID", None)

    result = await good_morning.send_good_morning(bot)

    assert result is False
    bot.send_photo.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_good_morning_sends_photo(tmp_path, monkeypatch):
    img_dir = tmp_path / "img"
    img_dir.mkdir()
    (img_dir / "pic.jpg").write_bytes(b"fake")
    (img_dir / "note.txt").write_text("skip me")

    bot = AsyncMock()
    monkeypatch.setattr(good_morning, "GOOD_MORNING_CHAT_ID", "123")
    monkeypatch.setattr(good_morning, "IMAGES_DIR", str(img_dir))

    result = await good_morning.send_good_morning(bot)

    assert result is True
    bot.send_photo.assert_awaited_once()
    kwargs = bot.send_photo.await_args_list[0].kwargs
    assert kwargs["chat_id"] == "123"
    assert kwargs["caption"] == "Доброе утро"
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from bot.utils import good_morning


@pytest.mark.asyncio
async def test_send_good_morning_no_chat_id(tmp_path, monkeypatch):
    """Если чат не задан, сообщение не отправляется."""
    # Папка с картинками не важна, главное — отсутствие chat_id
    monkeypatch.setattr(good_morning, "GOOD_MORNING_CHAT_ID", None)

    bot = AsyncMock()

    result = await good_morning.send_good_morning(bot)

    bot.send_photo.assert_not_awaited()
    assert result is False


@pytest.mark.asyncio
async def test_send_good_morning_with_random_image(tmp_path, monkeypatch):
    """При заданном чате и наличии картинок отправляется фото с подписью."""
    # Создаём временную папку с картинками
    img_dir = tmp_path / "img"
    img_dir.mkdir()
    # Подходящий по расширению файл
    image_path = img_dir / "morning.jpg"
    image_path.write_bytes(b"fake image content")
    # Файл с неподходящим расширением, чтобы проверить фильтрацию
    (img_dir / "readme.txt").write_text("not an image")

    monkeypatch.setattr(good_morning, "IMAGES_DIR", str(img_dir))
    monkeypatch.setattr(good_morning, "GOOD_MORNING_CHAT_ID", "12345")

    bot = AsyncMock()

    result = await good_morning.send_good_morning(bot)

    bot.send_photo.assert_awaited_once()
    call = bot.send_photo.await_args_list[0]

    # Проверяем, что отправка идёт в нужный чат с правильной подписью
    assert call.kwargs["chat_id"] == "12345"
    assert call.kwargs["caption"] == "Доброе утро"
    assert result is True


