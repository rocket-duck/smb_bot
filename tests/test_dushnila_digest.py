"""Unit tests for bot/utils/dushnila_digest.py."""

from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bot.config import flags
from bot.config import settings as settings_module
from bot.database import Base
from bot.utils import dushnila_digest, dushnila_engine


@pytest_asyncio.fixture
async def dushnila_db(monkeypatch):
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    from bot import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    monkeypatch.setattr(dushnila_engine, "SessionLocal", TestingSessionLocal)
    yield TestingSessionLocal
    await engine.dispose()


def _set_env(monkeypatch, nfsw_chat_id="123"):
    monkeypatch.setenv("BOT_USERNAME", "test-bot")
    monkeypatch.setenv("API_TOKEN", "test-token")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai")
    if nfsw_chat_id is None:
        monkeypatch.delenv("NFSW_CHAT_ID", raising=False)
    else:
        monkeypatch.setenv("NFSW_CHAT_ID", nfsw_chat_id)
    settings_module.get_settings.cache_clear()


@pytest.mark.asyncio
async def test_send_digest_disabled_flag(monkeypatch, dushnila_db):
    monkeypatch.setattr(flags, "DUSHNILA_ENABLE", False)
    _set_env(monkeypatch)
    bot = AsyncMock()
    result = await dushnila_digest.send_dushnila_digest(bot)
    assert result is False
    bot.send_message.assert_not_awaited()
    monkeypatch.setattr(flags, "DUSHNILA_ENABLE", True)


@pytest.mark.asyncio
async def test_send_digest_no_chat_configured(monkeypatch, dushnila_db):
    _set_env(monkeypatch, nfsw_chat_id=None)
    bot = AsyncMock()
    result = await dushnila_digest.send_dushnila_digest(bot)
    assert result is False
    bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_digest_no_activity_skips_silently(monkeypatch, dushnila_db):
    _set_env(monkeypatch)
    bot = AsyncMock()
    result = await dushnila_digest.send_dushnila_digest(bot)
    assert result is False
    bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_digest_sends_totals(monkeypatch, dushnila_db):
    from bot.models import DushnilaEvent, Participant

    _set_env(monkeypatch)

    async with dushnila_db() as session:
        session.add(
            Participant(chat_id=123, user_id=7, full_name="Masha", username="masha")
        )
        session.add(
            DushnilaEvent(
                chat_id=123,
                user_id=7,
                full_name="Masha",
                username="masha",
                category="phrase",
                reason="фраза «это баг»",
                points=5,
            )
        )
        await session.commit()

    bot = AsyncMock()
    result = await dushnila_digest.send_dushnila_digest(bot)

    assert result is True
    bot.send_message.assert_awaited_once()
    kwargs = bot.send_message.await_args_list[0].kwargs
    assert kwargs["chat_id"] == 123
    assert "Masha" in kwargs["text"]
    assert "5 баллов" in kwargs["text"]
