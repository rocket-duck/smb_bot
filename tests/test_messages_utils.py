"""Unit tests for utility functions in bot/messages/messages.py."""
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import bot.config.flags as flag
from bot.messages.messages import (
    extract_keyword,
    filter_recent_links,
    format_response,
    no_fsm_filter,
    should_ignore_bot_mention,
    should_process_text,
)


# ── should_ignore_bot_mention ─────────────────────────────────────────────────


def test_should_ignore_bot_mention_exact_match():
    assert should_ignore_bot_mention("@mybot", "mybot") is True


def test_should_ignore_bot_mention_case_insensitive():
    assert should_ignore_bot_mention("@MyBot", "mybot") is True


def test_should_ignore_bot_mention_partial_text():
    assert should_ignore_bot_mention("hey @mybot help me", "mybot") is False


def test_should_ignore_bot_mention_other_bot():
    assert should_ignore_bot_mention("@otherbot", "mybot") is False


def test_should_ignore_bot_mention_tuple_username():
    """bot_username может быть кортежем — берётся первый элемент."""
    assert should_ignore_bot_mention("@mybot", ("mybot",)) is True


# ── should_process_text ───────────────────────────────────────────────────────


def test_should_process_text_slash_command():
    assert should_process_text("/start") is False


def test_should_process_text_bot_mention(monkeypatch):
    from bot.messages import messages as msg_module

    monkeypatch.setattr(msg_module, "settings", SimpleNamespace(bot_username="mybot"))
    assert should_process_text("@mybot") is False


def test_should_process_text_flag_disabled(monkeypatch):
    from bot.messages import messages as msg_module

    monkeypatch.setattr(msg_module, "settings", SimpleNamespace(bot_username="mybot"))
    monkeypatch.setattr(flag, "KEYWORD_RESPONSES_ENABLE", False)
    assert should_process_text("some text") is False


def test_should_process_text_normal_message(monkeypatch):
    from bot.messages import messages as msg_module

    monkeypatch.setattr(msg_module, "settings", SimpleNamespace(bot_username="mybot"))
    monkeypatch.setattr(flag, "KEYWORD_RESPONSES_ENABLE", True)
    assert should_process_text("how to fix B0101") is True


# ── extract_keyword ───────────────────────────────────────────────────────────


def test_extract_keyword_strips_and_lowercases():
    message = SimpleNamespace(text="  Hello World  ")
    assert extract_keyword(message) == "hello world"


def test_extract_keyword_none_text():
    message = SimpleNamespace(text=None)
    assert extract_keyword(message) == ""


def test_extract_keyword_already_lowercase():
    message = SimpleNamespace(text="b0101")
    assert extract_keyword(message) == "b0101"


# ── format_response ───────────────────────────────────────────────────────────


def test_format_response_header():
    result = format_response([("A", "http://a.com")])
    assert result.startswith("Возможно это поможет разобраться:\n")


def test_format_response_multiple_items():
    result = format_response([("Doc A", "http://a.com"), ("Doc B", "http://b.com")])
    assert "Doc A: http://a.com" in result
    assert "Doc B: http://b.com" in result


def test_format_response_single_item():
    result = format_response([("Only", "http://only.com")])
    assert "Only: http://only.com" in result


# ── filter_recent_links ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_filter_recent_links_all_pass(monkeypatch):
    from bot.messages import messages as msg_module

    class FakeCache:
        async def is_recent_link(self, chat_id, url):
            return False

        async def set_recent_link(self, chat_id, url, ttl):
            pass

    monkeypatch.setattr(msg_module, "cache", FakeCache())

    results = [("A", "http://a.com"), ("B", "http://b.com")]
    assert await filter_recent_links(1, results) == results


@pytest.mark.asyncio
async def test_filter_recent_links_excludes_recent(monkeypatch):
    from bot.messages import messages as msg_module

    class FakeCache:
        async def is_recent_link(self, chat_id, url):
            return url == "http://a.com"

        async def set_recent_link(self, chat_id, url, ttl):
            pass

    monkeypatch.setattr(msg_module, "cache", FakeCache())

    results = [("A", "http://a.com"), ("B", "http://b.com")]
    filtered = await filter_recent_links(1, results)
    assert filtered == [("B", "http://b.com")]


@pytest.mark.asyncio
async def test_filter_recent_links_all_recent(monkeypatch):
    from bot.messages import messages as msg_module

    class FakeCache:
        async def is_recent_link(self, chat_id, url):
            return True

        async def set_recent_link(self, chat_id, url, ttl):
            pass

    monkeypatch.setattr(msg_module, "cache", FakeCache())

    results = [("A", "http://a.com"), ("B", "http://b.com")]
    assert await filter_recent_links(1, results) == []


# ── no_fsm_filter ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_no_fsm_filter_passes_normal_text():
    state = AsyncMock()
    state.get_state = AsyncMock(return_value=None)
    assert await no_fsm_filter(SimpleNamespace(text="hello"), state) is True


@pytest.mark.asyncio
async def test_no_fsm_filter_blocks_active_state():
    state = AsyncMock()
    state.get_state = AsyncMock(return_value="SomeState:waiting")
    assert await no_fsm_filter(SimpleNamespace(text="hello"), state) is False


@pytest.mark.asyncio
async def test_no_fsm_filter_blocks_command():
    state = AsyncMock()
    state.get_state = AsyncMock(return_value=None)
    assert await no_fsm_filter(SimpleNamespace(text="/start"), state) is False


@pytest.mark.asyncio
async def test_no_fsm_filter_blocks_empty_text():
    state = AsyncMock()
    state.get_state = AsyncMock(return_value=None)
    assert await no_fsm_filter(SimpleNamespace(text=None), state) is False
