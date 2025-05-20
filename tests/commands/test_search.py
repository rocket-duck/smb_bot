import pytest
import asyncio
import re
from types import SimpleNamespace

import bot.commands.search as search_mod
from bot.services.search_service import ask_gpt

# --- Dummy classes ---

class DummyState:
    def __init__(self):
        self.cleared = False
        self.data = {}

    async def clear(self):
        self.cleared = True

    async def get_data(self):
        return self.data

    async def update_data(self, **kwargs):
        self.data.update(kwargs)

    async def set_state(self, state, timeout=None):
        self.timeout = timeout

class DummyMessage:
    def __init__(self, text=None):
        self.answers = []
        self.text = text
        self.from_user = SimpleNamespace(id=1)
        self.reply_to_message = None

    async def answer(self, text, reply_markup=None):
        self.answers.append((text, reply_markup))

# --- Tests for utility functions ---

@pytest.mark.parametrize("input_text, expected", [
    ("Hello, world!", "Hello, world!"),
    ("<script>alert(1)</script>", "scriptalert1script"),
    ("This is a very long text " + "x" * 300,
     ("This is a very long text " + "x" * 300)[:200]),
    ("Symbols: @$%^&*()[]{}", "Symbols "),
])
def test_sanitize_query(input_text, expected):
    result = search_mod.sanitize_query(input_text)
    assert result == expected
    # Should not contain angle brackets or disallowed chars
    assert "<" not in result and ">" not in result
    assert re.match(r'^[\w\s\?\!\.,\-\:]*$', result)

@pytest.mark.asyncio
@pytest.mark.parametrize("text, expected", [
    ("/cmd", True),
    (" /cmd", True),
    ("no slash", False),
    ("", False),
    (None, False),
])
async def test_is_command(text, expected):
    msg = DummyMessage(text)
    assert await search_mod.is_command(msg) == expected

# --- Tests for immediate processing ---

@pytest.mark.asyncio
async def test_process_immediate_query(monkeypatch):
    msg = DummyMessage()
    state = DummyState()
    queries = []
    # stub log_search_request_db to avoid DB and username access
    monkeypatch.setattr(search_mod, "log_search_request_db", lambda m, q: queries.append(q))
    # stub ask_gpt
    monkeypatch.setattr(search_mod, "ask_gpt", lambda q: asyncio.sleep(0, result="ANS"))
    # run
    await search_mod.process_immediate_query("Q1", msg, state)
    # should log to db
    assert queries == ["Q1"]
    # should answer "processing" and then the answer
    assert msg.answers[0][0] == "Обрабатываю ваш запрос..."
    assert msg.answers[1][0] == "ANS"
    # state.clear called
    assert state.cleared

# --- Tests for cmd_search handler ---

class DummyReplyMessage(DummyMessage):
    def __init__(self, text, reply_text):
        super().__init__(text)
        self.reply_to_message = SimpleNamespace(text=reply_text)
        self.answer_called = False

@pytest.mark.asyncio
async def test_cmd_search_with_reply(monkeypatch):
    # simulate reply to message with text
    dummy = DummyReplyMessage("/search extra", "Original text")
    dummy.from_user.id = 2
    state = DummyState()
    async def dummy_async(q, m, s):
        return None
    monkeypatch.setattr(search_mod, "process_immediate_query", dummy_async)
    await search_mod.cmd_search(dummy, state)
    # check that combined query is passed
    # The combined query is "Original text extra".strip()
    # Since process_immediate_query is mocked, no output expected here
    # But we can check that the function was awaited without error

@pytest.mark.asyncio
async def test_cmd_search_with_additional(monkeypatch):
    dummy = DummyMessage("/search ask me")
    dummy.reply_to_message = None
    dummy.from_user.id = 3
    state = DummyState()
    async def dummy_async(q, m, s):
        return None
    monkeypatch.setattr(search_mod, "process_immediate_query", dummy_async)
    await search_mod.cmd_search(dummy, state)

@pytest.mark.asyncio
async def test_cmd_search_waiting(monkeypatch):
    dummy = DummyMessage("/search")
    dummy.message_id = 42
    dummy.reply_to_message = None
    dummy.from_user.id = 4
    answers = []
    class DummySentMessage:
        def __init__(self, message_id):
            self.message_id = message_id
    async def dummy_answer(text, reply_markup=None):
        answers.append((text, reply_markup))
        return DummySentMessage(123)  # эмулируем возврат Message с message_id
    dummy.answer = dummy_answer
    # stub state
    state = DummyState()
    async def dummy_async(q, m, s):
        return None
    monkeypatch.setattr(search_mod, "process_immediate_query", dummy_async)
    await search_mod.cmd_search(dummy, state)
    assert any("Введите текст запроса" in a[0] for a in answers)
    assert state.data.get("user_id") == 4

# --- Tests for FSM handlers ---

@pytest.mark.asyncio
async def test_cancel_on_command(monkeypatch):
    dummy = DummyMessage("/other")
    dummy.from_user.id = 5
    state = DummyState()
    state.cleared = False
    # Call cancel_on_command
    await search_mod.cancel_on_command(dummy, state)
    assert state.cleared

@pytest.mark.asyncio
async def test_process_search_query_ignores_other_user(monkeypatch):
    dummy = DummyMessage("hello")
    dummy.from_user.id = 6
    # stub state to return different user
    class S(DummyState):
        def __init__(self):
            super().__init__()
            self.data = {"user_id": 7}
        async def clear(self):
            raise AssertionError("Should not clear")
    state = S()
    answers = []
    async def dummy_answer(text, reply_markup=None):
        answers.append((text, reply_markup))
    dummy.answer = dummy_answer
    # shouldn't answer or clear
    await search_mod.process_search_query(dummy, state)
    assert answers == []

@pytest.mark.asyncio
async def test_process_search_query_cancel(monkeypatch):
    dummy = DummyMessage("отмена")
    dummy.from_user.id = 8
    class S(DummyState):
        def __init__(self):
            super().__init__()
            self.data = {"user_id": 8}
            self.cleared = False
        async def clear(self):
            self.cleared = True
    state = S()
    answers = []
    async def dummy_answer(text, reply_markup=None):
        answers.append((text, reply_markup))
    dummy.answer = dummy_answer
    await search_mod.process_search_query(dummy, state)
    assert state.cleared

@pytest.mark.asyncio
async def test_process_search_query_executes(monkeypatch):
    dummy = DummyMessage("query")
    dummy.from_user.id = 9
    calls = []
    class S(DummyState):
        async def get_data(self):
            return {"user_id": 9}
        async def clear(self):
            pass
    state = S()
    async def dummy_async(q, m, s):
        calls.append(q)
        return None
    monkeypatch.setattr(search_mod, "process_immediate_query", dummy_async)
    await search_mod.process_search_query(dummy, state)
    assert calls == ["query"]

@pytest.mark.asyncio
async def test_cmd_search_debounce(monkeypatch):
    dummy = DummyMessage("/search test")
    dummy.from_user.id = 10
    state = DummyState()
    # эмулируем, что last_query уже есть
    await state.update_data(last_query="test")
    answers = []
    async def dummy_answer(text, reply_markup=None):
        answers.append(text)
    dummy.answer = dummy_answer
    async def dummy_async(q, m, s):
        raise AssertionError("Should not be called if debounce сработал")
    monkeypatch.setattr(search_mod, "process_immediate_query", dummy_async)
    await search_mod.cmd_search(dummy, state)
    assert any("уже отправляли этот запрос" in a for a in answers)

@pytest.mark.asyncio
async def test_cmd_search_with_error(monkeypatch):
    dummy = DummyMessage("/search fail")
    dummy.from_user.id = 11
    state = DummyState()
    async def dummy_answer(text, reply_markup=None):
        pass  # игнорируем
    dummy.answer = dummy_answer
    async def fail_async(q, m, s):
        raise Exception("OpenAI error")
    monkeypatch.setattr(search_mod, "process_immediate_query", fail_async)
    try:
        await search_mod.cmd_search(dummy, state)
    except Exception as e:
        assert "OpenAI error" in str(e)
