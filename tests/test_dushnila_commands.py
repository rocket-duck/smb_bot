"""Unit tests for bot/commands/dushnila_*.py."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from bot.commands import dushnila_me, dushnila_reset_week, dushnila_weekly, dushnila_why
from bot.models import DushnilaEvent


def _message(**overrides):
    defaults = dict(
        chat=SimpleNamespace(type="group", id=1, title="Team"),
        from_user=SimpleNamespace(id=7, full_name="Masha", username="masha"),
        text="",
        answer=AsyncMock(),
        bot=AsyncMock(),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ── /dushnila_weekly ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dushnila_weekly_private_chat():
    message = _message(chat=SimpleNamespace(type="private", id=1))
    await dushnila_weekly.handle_dushnila_weekly(message)
    message.answer.assert_awaited_once_with(
        "Эта команда доступна только в групповых чатах."
    )


@pytest.mark.asyncio
async def test_dushnila_weekly_empty(monkeypatch):
    monkeypatch.setattr(
        dushnila_weekly, "get_weekly_totals", AsyncMock(return_value=[])
    )
    message = _message()
    await dushnila_weekly.handle_dushnila_weekly(message)
    message.answer.assert_awaited_once_with(
        "На этой неделе пока нет активности душнил."
    )


@pytest.mark.asyncio
async def test_dushnila_weekly_formats_top(monkeypatch):
    totals = [
        (1, "Павел", "pavel", 428),
        (2, "Семен", "semen", 311),
    ]
    monkeypatch.setattr(
        dushnila_weekly, "get_weekly_totals", AsyncMock(return_value=totals)
    )
    message = _message()
    await dushnila_weekly.handle_dushnila_weekly(message)
    text = message.answer.await_args_list[0].args[0]
    assert "🏆 Топ душнил недели" in text
    assert "1. Павел (pavel) — 428 баллов" in text
    assert "2. Семен (semen) — 311 баллов" in text


# ── /dushnila_me ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dushnila_me_private_chat():
    message = _message(chat=SimpleNamespace(type="private", id=1))
    await dushnila_me.handle_dushnila_me(message)
    message.answer.assert_awaited_once_with(
        "Эта команда доступна только в групповых чатах."
    )


@pytest.mark.asyncio
async def test_dushnila_me_reports_total(monkeypatch):
    monkeypatch.setattr(
        dushnila_me, "get_personal_weekly_total", AsyncMock(return_value=42)
    )
    message = _message()
    await dushnila_me.handle_dushnila_me(message)
    text = message.answer.await_args_list[0].args[0]
    assert "42 балла" in text


# ── /dushnila_why ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dushnila_why_private_chat():
    message = _message(chat=SimpleNamespace(type="private", id=1))
    await dushnila_why.handle_dushnila_why(message)
    message.answer.assert_awaited_once_with(
        "Эта команда доступна только в групповых чатах."
    )


@pytest.mark.asyncio
async def test_dushnila_why_missing_argument():
    message = _message(text="/dushnila_why")
    await dushnila_why.handle_dushnila_why(message)
    message.answer.assert_awaited_once_with("Использование: /dushnila_why @username")


@pytest.mark.asyncio
async def test_dushnila_why_unknown_username(monkeypatch):
    monkeypatch.setattr(
        dushnila_why, "find_participant_by_username", AsyncMock(return_value=None)
    )
    message = _message(text="/dushnila_why @ghost")
    await dushnila_why.handle_dushnila_why(message)
    text = message.answer.await_args_list[0].args[0]
    assert "Не нашёл участника" in text


@pytest.mark.asyncio
async def test_dushnila_why_formats_events(monkeypatch):
    participant = SimpleNamespace(user_id=7, full_name="Алексей", username="alexey")
    monkeypatch.setattr(
        dushnila_why,
        "find_participant_by_username",
        AsyncMock(return_value=participant),
    )
    events = [
        DushnilaEvent(points=25, reason="11 сообщений подряд"),
        DushnilaEvent(points=12, reason="8 вопросов в сообщении"),
        DushnilaEvent(points=-5, reason="фраза «всё ок»"),
    ]
    monkeypatch.setattr(
        dushnila_why, "get_today_events", AsyncMock(return_value=events)
    )
    message = _message(text="/dushnila_why @alexey")
    await dushnila_why.handle_dushnila_why(message)
    text = message.answer.await_args_list[0].args[0]
    assert "🔥 Алексей сегодня:" in text
    assert "+25 за 11 сообщений подряд" in text
    assert "-5 за фраза «всё ок»" in text


# ── /dushnila_reset_week ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dushnila_reset_week_private_chat():
    message = _message(chat=SimpleNamespace(type="private", id=1))
    await dushnila_reset_week.handle_dushnila_reset_week(message)
    message.answer.assert_awaited_once_with(
        "Эта команда доступна только в групповых чатах."
    )


@pytest.mark.asyncio
async def test_dushnila_reset_week_rejects_non_admin(monkeypatch):
    monkeypatch.setattr(
        dushnila_reset_week, "is_chat_admin", AsyncMock(return_value=False)
    )
    reset_mock = AsyncMock()
    monkeypatch.setattr(dushnila_reset_week, "reset_week", reset_mock)
    message = _message()
    await dushnila_reset_week.handle_dushnila_reset_week(message)
    reset_mock.assert_not_awaited()
    text = message.answer.await_args_list[0].args[0]
    assert "администратор" in text


@pytest.mark.asyncio
async def test_dushnila_reset_week_admin_resets(monkeypatch):
    monkeypatch.setattr(
        dushnila_reset_week, "is_chat_admin", AsyncMock(return_value=True)
    )
    reset_mock = AsyncMock()
    monkeypatch.setattr(dushnila_reset_week, "reset_week", reset_mock)
    message = _message()
    await dushnila_reset_week.handle_dushnila_reset_week(message)
    reset_mock.assert_awaited_once_with(1)
    message.answer.assert_awaited_once_with("Недельный рейтинг душнил сброшен.")
