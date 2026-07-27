"""Unit tests for bot/utils/best_qa_digest.py."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bot.commands import best_qa
from bot.config import flags
from bot.config import settings as settings_module
from bot.database import Base
from bot.utils import best_qa_digest, game_engine


@pytest_asyncio.fixture
async def best_qa_db(monkeypatch):
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    from bot import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    monkeypatch.setattr(game_engine, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(best_qa, "SUSPENSE_SECONDS", 0)
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


def _bot_with_chat_title(title="Team"):
    bot = AsyncMock()
    bot.get_chat = AsyncMock(return_value=SimpleNamespace(title=title))
    return bot


@pytest.mark.asyncio
async def test_run_daily_best_qa_disabled_flag(monkeypatch, best_qa_db):
    monkeypatch.setattr(flags, "BEST_QA_ENABLE", False)
    _set_env(monkeypatch)
    bot = _bot_with_chat_title()
    await best_qa_digest.run_daily_best_qa(bot)
    bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_daily_best_qa_no_chat_configured(monkeypatch, best_qa_db):
    _set_env(monkeypatch, nfsw_chat_id=None)
    bot = _bot_with_chat_title()
    await best_qa_digest.run_daily_best_qa(bot)
    bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_daily_best_qa_no_participants(monkeypatch, best_qa_db):
    _set_env(monkeypatch)
    bot = _bot_with_chat_title()
    await best_qa_digest.run_daily_best_qa(bot)
    bot.send_message.assert_awaited_once_with(123, "Не нашёл участников для выбора.")


@pytest.mark.asyncio
async def test_run_daily_best_qa_picks_winner(monkeypatch, best_qa_db):
    from bot.models import Participant

    _set_env(monkeypatch)
    async with best_qa_db() as session:
        session.add(
            Participant(chat_id=123, user_id=7, full_name="Masha", username="masha")
        )
        await session.commit()

    monkeypatch.setattr(best_qa.random, "randint", lambda a, b: 1)

    bot = _bot_with_chat_title("Team")
    await best_qa_digest.run_daily_best_qa(bot)

    calls = bot.send_message.await_args_list
    assert len(calls) == 3
    assert calls[0].args[0] == 123
    assert "Masha" in calls[0].args[1]
    assert calls[1].args == (123, "🎲 Бросаем кубик: 1d1...")
    assert "Masha" in calls[2].args[1]


@pytest.mark.asyncio
async def test_run_daily_best_qa_already_chosen(monkeypatch, best_qa_db):
    from bot.models import Participant

    _set_env(monkeypatch)
    async with best_qa_db() as session:
        session.add(
            Participant(chat_id=123, user_id=7, full_name="Masha", username="masha")
        )
        await session.commit()

    monkeypatch.setattr(best_qa.random, "randint", lambda a, b: 1)
    bot = _bot_with_chat_title("Team")
    await best_qa_digest.run_daily_best_qa(bot)
    bot.send_message.reset_mock()

    await best_qa_digest.run_daily_best_qa(bot)
    bot.send_message.assert_awaited_once()
    text = bot.send_message.await_args_list[0].args[1]
    assert "уже выбран" in text
