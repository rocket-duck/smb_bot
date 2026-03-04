"""Unit tests for bot/commands/best_qa.py and best_qa_stat.py."""
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from bot.commands import best_qa, best_qa_stat


# ── handle_best_qa ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_handle_best_qa_private_chat():
    """В личном чате команда возвращает сообщение об ограничении."""
    message = SimpleNamespace(
        chat=SimpleNamespace(type="private", id=1, title="Private"),
        answer=AsyncMock(),
    )
    await best_qa.handle_best_qa(message)
    message.answer.assert_awaited_once_with("Эта команда доступна только в групповых чатах.")


@pytest.mark.asyncio
async def test_handle_best_qa_already_chosen_shows_existing_winner(monkeypatch):
    """Если победитель уже выбран сегодня, бот показывает его имя."""
    monkeypatch.setattr(best_qa, "is_new_day", AsyncMock(return_value=False))
    winner = SimpleNamespace(winner_user_id=42, winner_full_name="Vasya")
    monkeypatch.setattr(best_qa, "get_last_winner", AsyncMock(return_value=winner))
    monkeypatch.setattr(best_qa, "format_winner_mention", lambda uid, name: f"@{name}")

    message = SimpleNamespace(
        chat=SimpleNamespace(type="group", id=1, title="Test"),
        answer=AsyncMock(),
    )
    await best_qa.handle_best_qa(message)

    text = message.answer.await_args_list[0].args[0]
    assert "уже выбран" in text
    assert "@Vasya" in text


@pytest.mark.asyncio
async def test_handle_best_qa_already_chosen_no_winner_silent(monkeypatch):
    """Если is_new_day=False и в БД нет записи — бот молчит."""
    monkeypatch.setattr(best_qa, "is_new_day", AsyncMock(return_value=False))
    monkeypatch.setattr(best_qa, "get_last_winner", AsyncMock(return_value=None))

    message = SimpleNamespace(
        chat=SimpleNamespace(type="group", id=1, title="Test"),
        answer=AsyncMock(),
    )
    await best_qa.handle_best_qa(message)
    message.answer.assert_not_awaited()


@pytest.mark.asyncio
async def test_handle_best_qa_no_participants(monkeypatch):
    """Если участников нет, бот сообщает об этом."""
    monkeypatch.setattr(best_qa, "is_new_day", AsyncMock(return_value=True))
    monkeypatch.setattr(best_qa, "get_random_participant", AsyncMock(return_value=None))

    message = SimpleNamespace(
        chat=SimpleNamespace(type="group", id=1, title="Test"),
        answer=AsyncMock(),
    )
    await best_qa.handle_best_qa(message)
    message.answer.assert_awaited_once_with("Не нашёл участников для выбора.")


@pytest.mark.asyncio
async def test_handle_best_qa_new_winner_announced(monkeypatch):
    """При новом дне выбирается победитель и отправляется сообщение."""
    monkeypatch.setattr(best_qa, "is_new_day", AsyncMock(return_value=True))
    participant = SimpleNamespace(user_id=7, full_name="Masha", username="masha")
    monkeypatch.setattr(best_qa, "get_random_participant", AsyncMock(return_value=participant))
    monkeypatch.setattr(best_qa, "update_last_winner", AsyncMock())
    monkeypatch.setattr(best_qa, "update_winner_stats", AsyncMock())
    monkeypatch.setattr(best_qa, "format_winner_mention", lambda uid, name: f"@{name}")

    message = SimpleNamespace(
        chat=SimpleNamespace(type="group", id=1, title="Team"),
        answer=AsyncMock(),
    )
    await best_qa.handle_best_qa(message)

    best_qa.update_last_winner.assert_awaited_once()
    best_qa.update_winner_stats.assert_awaited_once()
    text = message.answer.await_args_list[0].args[0]
    assert "@Masha" in text
    assert "лучший тестировщик" in text


# ── format_stats ──────────────────────────────────────────────────────────────


def test_format_stats_with_username():
    stats = [
        SimpleNamespace(chat_title="Test Chat", full_name="Alice", username="alice", wins=5)
    ]
    result = best_qa_stat.format_stats(
        SimpleNamespace(chat=SimpleNamespace(title="Test Chat")), stats
    )
    assert "Test Chat" in result
    assert "Alice" in result
    assert "(username: alice)" in result
    assert "5 побед" in result


def test_format_stats_no_username():
    stats = [
        SimpleNamespace(chat_title="Chat", full_name="Bob", username="", wins=1)
    ]
    result = best_qa_stat.format_stats(
        SimpleNamespace(chat=SimpleNamespace(title="Chat")), stats
    )
    assert "Bob" in result
    assert "username" not in result
    assert "1 победа" in result


def test_format_stats_falls_back_to_message_title():
    """Если chat_title в записи пустой — берётся название из message.chat.title."""
    stats = [
        SimpleNamespace(chat_title="", full_name="Eve", username="", wins=2)
    ]
    result = best_qa_stat.format_stats(
        SimpleNamespace(chat=SimpleNamespace(title="Fallback")), stats
    )
    assert "Fallback" in result


def test_format_stats_multiple_winners():
    stats = [
        SimpleNamespace(chat_title="Chat", full_name="Alice", username="", wins=3),
        SimpleNamespace(chat_title="Chat", full_name="Bob", username="", wins=1),
    ]
    result = best_qa_stat.format_stats(
        SimpleNamespace(chat=SimpleNamespace(title="Chat")), stats
    )
    assert "Alice" in result
    assert "Bob" in result


# ── handle_best_qa_stat ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_handle_best_qa_stat_private_chat():
    message = SimpleNamespace(
        chat=SimpleNamespace(type="private", id=1),
        answer=AsyncMock(),
    )
    await best_qa_stat.handle_best_qa_stat(message)
    message.answer.assert_awaited_once_with("Статистика доступна только для групповых чатов.")


@pytest.mark.asyncio
async def test_handle_best_qa_stat_empty(monkeypatch):
    monkeypatch.setattr(best_qa_stat, "get_stats", AsyncMock(return_value=[]))
    message = SimpleNamespace(
        chat=SimpleNamespace(type="group", id=1),
        answer=AsyncMock(),
    )
    await best_qa_stat.handle_best_qa_stat(message)
    message.answer.assert_awaited_once_with("Статистика по лучшим тестировщикам пока пуста.")


@pytest.mark.asyncio
async def test_handle_best_qa_stat_with_data(monkeypatch):
    stats = [
        SimpleNamespace(chat_title="Team", full_name="Alice", username="alice", wins=3)
    ]
    monkeypatch.setattr(best_qa_stat, "get_stats", AsyncMock(return_value=stats))
    message = SimpleNamespace(
        chat=SimpleNamespace(type="group", id=1, title="Team"),
        answer=AsyncMock(),
    )
    await best_qa_stat.handle_best_qa_stat(message)
    message.answer.assert_awaited_once()
    response = message.answer.await_args_list[0].args[0]
    assert "Alice" in response
    assert "Team" in response
