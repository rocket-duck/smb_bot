from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bot.database import Base
from bot.utils import good_morning


@pytest_asyncio.fixture
async def gm_db(monkeypatch):
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    from bot import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    monkeypatch.setattr(good_morning, "SessionLocal", TestingSessionLocal)
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_send_good_morning_no_chat_id(tmp_path, monkeypatch, gm_db):
    bot = AsyncMock()
    monkeypatch.setattr(good_morning, "GOOD_MORNING_CHAT_ID", None)
    monkeypatch.setattr(good_morning, "IMAGES_DIR", str(tmp_path / "img"))

    result = await good_morning.send_good_morning(bot)

    assert result is False
    bot.send_photo.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_good_morning_sends_photo(tmp_path, monkeypatch, gm_db):
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


@pytest.mark.asyncio
async def test_images_do_not_repeat_until_cycle_complete(tmp_path,
                                                         monkeypatch,
                                                         gm_db):
    img_dir = tmp_path / "img"
    img_dir.mkdir()
    (img_dir / "a.jpg").write_bytes(b"a")
    (img_dir / "b.jpg").write_bytes(b"b")

    bot = AsyncMock()
    monkeypatch.setattr(good_morning, "GOOD_MORNING_CHAT_ID", "chat")
    monkeypatch.setattr(good_morning, "IMAGES_DIR", str(img_dir))

    def pick_first(sequence):
        return sorted(sequence, key=lambda item: item.filename)[0]

    monkeypatch.setattr(good_morning.random, "choice", pick_first)

    await good_morning.send_good_morning(bot)
    await good_morning.send_good_morning(bot)
    await good_morning.send_good_morning(bot)

    assert bot.send_photo.await_count == 3
    paths = [call.kwargs["photo"].path for call in bot.send_photo.await_args_list]
    assert paths[0].endswith("a.jpg")
    assert paths[1].endswith("b.jpg")
    assert paths[2].endswith("a.jpg")

