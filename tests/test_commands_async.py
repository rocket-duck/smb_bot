from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bot.commands import best_qa, search
from bot.database import Base
from bot.models import SearchLog


@pytest_asyncio.fixture
async def search_session_local(monkeypatch):
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    monkeypatch.setattr(search, "SessionLocal", TestingSessionLocal)
    yield TestingSessionLocal
    await engine.dispose()


@pytest.mark.asyncio
async def test_process_immediate_query(monkeypatch):
    message = SimpleNamespace(
        from_user=SimpleNamespace(id=1, username="user", full_name="User"),
        date=None,
        answer=AsyncMock(),
    )
    state = SimpleNamespace(clear=AsyncMock())

    async def fake_query_openai(user_query, message):
        return "result"

    async def fake_log_search_request_db(message, user_query):
        pass

    monkeypatch.setattr(search, "query_openai", fake_query_openai)
    monkeypatch.setattr(search, "log_search_request_db", fake_log_search_request_db)

    await search.process_immediate_query("hi", message, state)

    assert message.answer.await_count == 2
    assert message.answer.await_args_list[0].args[0] == "Обрабатываю ваш запрос..."
    assert message.answer.await_args_list[1].args[0] == "result"
    state.clear.assert_awaited_once()


@pytest.mark.asyncio
async def test_log_search_request_db(search_session_local):
    message = SimpleNamespace(
        from_user=SimpleNamespace(id=1, username="user", full_name="User"),
        date=datetime.now(),
    )

    await search.log_search_request_db(message, "hello")

    async with search_session_local() as session:
        result = await session.execute(select(SearchLog))
        log = result.scalars().first()
        assert log is not None
        assert log.user_id == 1
        assert log.query == "hello"


@pytest.mark.asyncio
async def test_handle_best_qa(monkeypatch):
    message = SimpleNamespace(
        chat=SimpleNamespace(id=1, title="Test", type="group"), answer=AsyncMock()
    )

    async def fake_is_new_day(chat_id):
        return True

    monkeypatch.setattr(best_qa, "is_new_day", fake_is_new_day)
    participant = SimpleNamespace(user_id="1", full_name="User", username="user")

    async def fake_get_random_participant(chat_id):
        return participant

    monkeypatch.setattr(best_qa, "get_random_participant", fake_get_random_participant)
    flags = {"lw": False, "ws": False}

    async def fake_update_last_winner(*a, **k):
        flags["lw"] = True

    async def fake_update_winner_stats(*a, **k):
        flags["ws"] = True

    monkeypatch.setattr(best_qa, "update_last_winner", fake_update_last_winner)
    monkeypatch.setattr(best_qa, "update_winner_stats", fake_update_winner_stats)
    monkeypatch.setattr(
        best_qa,
        "format_winner_mention",
        lambda uid, name: f"mention:{uid}",
    )

    await best_qa.handle_best_qa(message)

    message.answer.assert_awaited_once_with(
        "Сегодня лучший тестировщик mention:1 🎉", parse_mode="HTML"
    )
    assert flags["lw"] and flags["ws"]
