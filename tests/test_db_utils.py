import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.models import Chat, LastWinner, WinnerStats, Participant
from bot.utils import chat_manager, game_engine
from bot.database import Base


@pytest.fixture
def session_local(monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(
        bind=engine, autocommit=False, autoflush=False
    )
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(chat_manager, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(game_engine, "SessionLocal", TestingSessionLocal)
    return TestingSessionLocal


def test_add_remove_get_chats(session_local):
    chat_manager.add_chat(1, "Test Chat", "adder")
    with session_local() as db:
        chat = db.query(Chat).filter_by(chat_id="1").first()
        assert chat is not None
        assert chat.title == "Test Chat"
        assert chat.added_by == "adder"
        assert chat.deleted is False

    assert chat_manager.remove_chat(1, "remover") is True
    assert chat_manager.remove_chat(1, "remover") is False
    with session_local() as db:
        chat = db.query(Chat).filter_by(chat_id="1").first()
        assert chat.deleted is True
        assert chat.deleted_by == "remover"

    chats = chat_manager.get_all_chats()
    assert {"chat_id": "1", "title": "Test Chat", "deleted": True} in chats


def test_game_engine_updates_and_random(session_local):
    # update_last_winner and is_new_day
    game_engine.update_last_winner("1", "Chat", "u1", "User One", "user1")
    assert game_engine.is_new_day("1") is False
    with session_local() as db:
        last = db.query(LastWinner).filter_by(chat_id="1").first()
        assert last.winner_user_id == "u1"

    # update_winner_stats increments wins
    game_engine.update_winner_stats("1", "Chat", "u1", "User One", "user1")
    game_engine.update_winner_stats("1", "Chat", "u1", "User One", "user1")
    with session_local() as db:
        stats = (
            db.query(WinnerStats)
            .filter_by(chat_id="1", user_id="u1")
            .first()
        )
        assert stats.wins == 2

    # get_random_participant returns one of inserted participants
    with session_local() as db:
        db.add_all([
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
        ])
        db.commit()
    participant = game_engine.get_random_participant("1")
    assert participant.user_id in {"u1", "u2"}

    # is_new_day becomes True when last_datetime is in the past
    from datetime import timedelta
    with session_local() as db:
        last = db.query(LastWinner).filter_by(chat_id="1").first()
        last.last_datetime = last.last_datetime - timedelta(days=1)
        db.commit()
    assert game_engine.is_new_day("1") is True
