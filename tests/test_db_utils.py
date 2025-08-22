import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from datetime import datetime

from bot.models import Chat, LastWinner, WinnerStats, Participant
from bot.utils import chat_manager, game_engine, participants
from bot.database import Base


@pytest_asyncio.fixture
async def session_local(monkeypatch):
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    monkeypatch.setattr(chat_manager, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(game_engine, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(participants, "SessionLocal", TestingSessionLocal)
    yield TestingSessionLocal
    await engine.dispose()


@pytest.mark.asyncio
async def test_add_remove_get_chats(session_local):
    await chat_manager.add_chat_async(1, "Test Chat", "adder")
    async with session_local() as db:
        result = await db.execute(select(Chat).filter(Chat.chat_id == "1"))
        chat = result.scalars().first()
        assert chat is not None
        assert chat.title == "Test Chat"
        assert chat.added_by == "adder"
        assert chat.deleted is False

    assert await chat_manager.remove_chat_async(1, "remover") is True
    assert await chat_manager.remove_chat_async(1, "remover") is False
    async with session_local() as db:
        result = await db.execute(select(Chat).filter(Chat.chat_id == "1"))
        chat = result.scalars().first()
        assert chat.deleted is True
        assert chat.deleted_by == "remover"

    chats = await chat_manager.get_all_chats_async()
    assert {"chat_id": "1", "title": "Test Chat", "deleted": True} in chats


@pytest.mark.asyncio
async def test_add_chat_restores_deleted(session_local):
    await chat_manager.add_chat_async(1, "Test Chat", "adder")
    assert await chat_manager.remove_chat_async(1, "remover") is True

    # Попытка повторного добавления должна восстановить удалённый чат
    await chat_manager.add_chat_async(1, "Test Chat", "adder")

    async with session_local() as db:
        result = await db.execute(select(Chat).filter(Chat.chat_id == "1"))
        chat = result.scalars().first()
        assert chat is not None
        assert chat.deleted is False
        assert chat.deleted_by is None
        assert chat.deleted_at is None


@pytest.mark.asyncio
async def test_game_engine_updates_and_random(session_local):
    await game_engine.update_last_winner("1", "Chat", "u1", "User One", "user1")
    assert await game_engine.is_new_day("1") is False
    async with session_local() as db:
        result = await db.execute(select(LastWinner).filter(LastWinner.chat_id == "1"))
        last = result.scalars().first()
        assert last.winner_user_id == "u1"

    await game_engine.update_winner_stats("1", "Chat", "u1", "User One", "user1")
    await game_engine.update_winner_stats("1", "Chat", "u1", "User One", "user1")
    async with session_local() as db:
        result = await db.execute(
            select(WinnerStats).filter(
                WinnerStats.chat_id == "1", WinnerStats.user_id == "u1"
            )
        )
        stats = result.scalars().first()
        assert stats.wins == 2

    async with session_local() as db:
        db.add_all(
            [
                Participant(
                    chat_id="1",
                    user_id="u1",
                    full_name="User One",
                    username="user1",
                ),
                Participant(
                    chat_id="1",
                    user_id="u2",
                    full_name="User Two",
                    username="user2",
                ),
            ]
        )
        await db.commit()
    participant = await game_engine.get_random_participant("1")
    assert participant.user_id in {"u1", "u2"}

    from datetime import timedelta

    async with session_local() as db:
        result = await db.execute(select(LastWinner).filter(LastWinner.chat_id == "1"))
        last = result.scalars().first()
        last.last_datetime = last.last_datetime - timedelta(days=1)
        await db.commit()
    assert await game_engine.is_new_day("1") is True


@pytest.mark.asyncio
async def test_update_participant_sets_last_active(session_local):
    from types import SimpleNamespace

    message = SimpleNamespace(
        chat=SimpleNamespace(type="group", id=1, title="Test Chat"),
        from_user=SimpleNamespace(id=123, full_name="User", username="user"),
    )

    await participants.update_participant(message)

    async with session_local() as db:
        result = await db.execute(
            select(Participant).filter(
                Participant.chat_id == "1", Participant.user_id == "123"
            )
        )
        participant = result.scalars().first()
        assert participant is not None
        assert participant.last_active is not None


@pytest.mark.asyncio
async def test_update_participant_private_chat_noop(session_local):
    from types import SimpleNamespace

    message = SimpleNamespace(
        chat=SimpleNamespace(type="private", id=1, title="Private"),
        from_user=SimpleNamespace(id=123, full_name="User", username="user"),
    )

    await participants.update_participant(message)

    async with session_local() as db:
        result = await db.execute(select(Participant))
        assert result.scalars().all() == []


@pytest.mark.asyncio
async def test_update_participant_refreshes_last_active(session_local, monkeypatch):
    from types import SimpleNamespace

    message = SimpleNamespace(
        chat=SimpleNamespace(type="group", id=1, title="Test Chat"),
        from_user=SimpleNamespace(id=123, full_name="User", username="user"),
    )

    class FirstDatetime:
        @classmethod
        def utcnow(cls):
            return datetime(2023, 1, 1)

    monkeypatch.setattr(participants, "datetime", FirstDatetime)
    await participants.update_participant(message)

    async with session_local() as db:
        result = await db.execute(
            select(Participant).filter(
                Participant.chat_id == "1", Participant.user_id == "123"
            )
        )
        participant = result.scalars().first()
        old_last_active = participant.last_active

    class SecondDatetime:
        @classmethod
        def utcnow(cls):
            return datetime(2023, 1, 2)

    monkeypatch.setattr(participants, "datetime", SecondDatetime)
    await participants.update_participant(message)

    async with session_local() as db:
        result = await db.execute(
            select(Participant).filter(
                Participant.chat_id == "1", Participant.user_id == "123"
            )
        )
        participant = result.scalars().first()
        assert participant.last_active > old_last_active
