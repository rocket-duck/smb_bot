"""Unit tests for bot/commands/search.py."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from openai import BadRequestError, OpenAIError, RateLimitError

from bot.commands import search
from bot.config.flags import SEARCH_MAX_QUERY_LEN


def _http_response(status: int) -> httpx.Response:
    return httpx.Response(
        status,
        request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"),
    )


# ── process_immediate_query ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_process_immediate_query_too_long():
    """Запрос длиннее лимита → сообщение об ошибке, OpenAI не вызывается."""
    message = SimpleNamespace(answer=AsyncMock())
    state = SimpleNamespace(clear=AsyncMock())

    await search.process_immediate_query("x" * (SEARCH_MAX_QUERY_LEN + 1), message, state)

    assert message.answer.await_count == 1
    assert str(SEARCH_MAX_QUERY_LEN) in message.answer.await_args_list[0].args[0]
    state.clear.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_immediate_query_ok(monkeypatch):
    """Запрос в пределах лимита → логируется, отправляется ответ OpenAI."""
    message = SimpleNamespace(answer=AsyncMock(), from_user=SimpleNamespace(id=1, username="u", full_name="U"), date=None)
    state = SimpleNamespace(clear=AsyncMock())

    monkeypatch.setattr(search, "log_search_request_db", AsyncMock())
    monkeypatch.setattr(search, "query_openai", AsyncMock(return_value="answer"))

    await search.process_immediate_query("hi", message, state)

    assert message.answer.await_args_list[0].args[0] == "Обрабатываю ваш запрос..."
    assert message.answer.await_args_list[1].args[0] == "answer"
    state.clear.assert_awaited_once()


# ── query_openai error handling ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_query_openai_rate_limit_error():
    err = RateLimitError("rate limit", response=_http_response(429), body=None)
    with patch("openai.chat.completions.create", side_effect=err):
        result = await search.query_openai("test", SimpleNamespace())
    assert "квота" in result


@pytest.mark.asyncio
async def test_query_openai_bad_request_error():
    err = BadRequestError("bad request", response=_http_response(400), body=None)
    with patch("openai.chat.completions.create", side_effect=err):
        result = await search.query_openai("test", SimpleNamespace())
    assert "Некорректный" in result


@pytest.mark.asyncio
async def test_query_openai_generic_openai_error():
    err = OpenAIError("something went wrong")
    with patch("openai.chat.completions.create", side_effect=err):
        result = await search.query_openai("test", SimpleNamespace())
    assert "ошибка" in result.lower()


# ── process_search_query ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_process_search_query_ignores_other_user(monkeypatch):
    """Сообщение от другого пользователя игнорируется без ответа."""
    called = {"value": False}

    async def fake_process(query, message, state):
        called["value"] = True

    monkeypatch.setattr(search, "process_immediate_query", fake_process)

    state = AsyncMock()
    state.get_data = AsyncMock(return_value={"user_id": 1})
    message = SimpleNamespace(from_user=SimpleNamespace(id=2), text="query")

    await search.process_search_query(message, state)
    assert not called["value"]


@pytest.mark.asyncio
async def test_process_search_query_cancel():
    """«Отмена» очищает состояние и отвечает сообщением об отмене."""
    state = AsyncMock()
    state.get_data = AsyncMock(return_value={"user_id": 1})
    message = SimpleNamespace(
        from_user=SimpleNamespace(id=1),
        text="отмена",
        answer=AsyncMock(),
    )

    await search.process_search_query(message, state)

    message.answer.assert_awaited_once_with("Операция отменена.")
    state.clear.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_search_query_cancel_english():
    """«cancel» (англ.) тоже отменяет запрос."""
    state = AsyncMock()
    state.get_data = AsyncMock(return_value={"user_id": 5})
    message = SimpleNamespace(
        from_user=SimpleNamespace(id=5),
        text="Cancel",
        answer=AsyncMock(),
    )

    await search.process_search_query(message, state)

    message.answer.assert_awaited_once_with("Операция отменена.")


# ── cmd_search ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cmd_search_with_additional_text(monkeypatch):
    """Команда с текстом после /search немедленно запускает запрос."""
    called_with = {}

    async def fake_process(query, message, state):
        called_with["query"] = query

    monkeypatch.setattr(search, "process_immediate_query", fake_process)
    message = SimpleNamespace(
        text="/search hello world",
        from_user=SimpleNamespace(id=1),
        reply_to_message=None,
        answer=AsyncMock(),
    )

    await search.cmd_search(message, AsyncMock())
    assert called_with.get("query") == "hello world"


@pytest.mark.asyncio
async def test_cmd_search_with_reply(monkeypatch):
    """Команда в реплае использует текст реплая как запрос."""
    called_with = {}

    async def fake_process(query, message, state):
        called_with["query"] = query

    monkeypatch.setattr(search, "process_immediate_query", fake_process)
    message = SimpleNamespace(
        text="/search",
        from_user=SimpleNamespace(id=1),
        reply_to_message=SimpleNamespace(text="reply query"),
        answer=AsyncMock(),
    )

    await search.cmd_search(message, AsyncMock())
    assert called_with.get("query") == "reply query"


@pytest.mark.asyncio
async def test_cmd_search_reply_plus_additional_text(monkeypatch):
    """Текст реплая + доп. текст объединяются в запрос."""
    called_with = {}

    async def fake_process(query, message, state):
        called_with["query"] = query

    monkeypatch.setattr(search, "process_immediate_query", fake_process)
    message = SimpleNamespace(
        text="/search extra",
        from_user=SimpleNamespace(id=1),
        reply_to_message=SimpleNamespace(text="base"),
        answer=AsyncMock(),
    )

    await search.cmd_search(message, AsyncMock())
    assert called_with.get("query") == "base extra"


@pytest.mark.asyncio
async def test_cmd_search_no_text_enters_waiting_state(monkeypatch):
    """Без текста и реплая бот переходит в режим ожидания."""
    monkeypatch.setattr(search, "search_timeout", AsyncMock())
    monkeypatch.setattr(search, "_track_timeout_task", lambda t: None)

    message = SimpleNamespace(
        text="/search",
        from_user=SimpleNamespace(id=1),
        reply_to_message=None,
        answer=AsyncMock(),
    )
    state = AsyncMock()

    await search.cmd_search(message, state)

    message.answer.assert_awaited_once()
    state.set_state.assert_awaited_once()
