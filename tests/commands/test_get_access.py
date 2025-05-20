import pytest
from types import SimpleNamespace
import bot.commands.get_access as ga_mod
from bot.config.tokens import ADMIN_USER_ID

# A dummy Message with minimal attributes
class DummyMessage:
    def __init__(self, user_id=1):
        self.from_user = SimpleNamespace(id=user_id, full_name="Full", username="user")
        self.chat = SimpleNamespace(type="private", id=123)
        self.answers = []
        self.bot = SimpleNamespace(
            send_message=self._send_message
        )

    async def answer(self, text):
        self.answers.append(text)

    async def delete(self):
        pass

    async def _send_message(self, chat_id, text, reply_markup=None):
        if not hasattr(self, 'admin_requests'):
            self.admin_requests = []
        self.admin_requests.append((chat_id, text, reply_markup))

# A dummy CallbackQuery with minimal attributes
class DummyCallback:
    def __init__(self, admin_id=2, target_id=1):
        self.from_user = SimpleNamespace(id=admin_id, full_name="Admin", username="admin")
        self.message = SimpleNamespace(
            edit_reply_markup=lambda reply_markup=None: None
        )
        self.bot = SimpleNamespace(
            send_message=lambda chat_id, text: None
        )
        self.replies = []
        self.answer = self._answer
        # Simulated callback_data passed separately
        self.data = None

    async def _answer(self, text):
        self.replies.append(text)

@pytest.mark.asyncio
async def test_get_access_flag_disabled(monkeypatch):
    # Flag off => direct answer and no admin request
    monkeypatch.setattr(ga_mod, "GET_ACCESS_ENABLE", False)
    msg = DummyMessage()
    await ga_mod.handle_get_access(msg)
    assert msg.answers == ["Ожидайте предоставление доступа."]

@pytest.mark.asyncio
async def test_get_access_already_has(monkeypatch):
    # Flag on, has_access returns True => inform user
    monkeypatch.setattr(ga_mod, "GET_ACCESS_ENABLE", True)
    monkeypatch.setattr(ga_mod, "has_access", lambda uid: True)
    msg = DummyMessage()
    await ga_mod.handle_get_access(msg)
    assert msg.answers == ["Доступ уже предоставлен"]

@pytest.mark.asyncio
async def test_get_access_request_sent(monkeypatch):
    # Flag on, has_access returns False => send admin request
    monkeypatch.setattr(ga_mod, "GET_ACCESS_ENABLE", True)
    monkeypatch.setattr(ga_mod, "has_access", lambda uid: False)
    msg = DummyMessage()
    await ga_mod.handle_get_access(msg)
    assert "Ожидайте предоставление доступа." in msg.answers
    assert hasattr(msg, "admin_requests")
    admin_chat_id, text, kb = msg.admin_requests[0]
    assert admin_chat_id == ADMIN_USER_ID
    assert "Запрос на доступ!" in text

@pytest.mark.asyncio
async def test_handle_accept_callback(monkeypatch):
    # Simulate admin accepting
    cb = DummyCallback(admin_id=2, target_id=99)
    data = SimpleNamespace(action="accept", user_id="99")
    calls = []
    monkeypatch.setattr(ga_mod, "grant_access", lambda admin, tid: calls.append((admin, tid)))
    # Call handler directly
    await ga_mod.handle_accept_callback(cb, data)
    assert calls == [({"user_id": 2, "full_name": "Admin", "username": "admin"}, 99)]
    assert "Доступ предоставлен." in cb.replies

@pytest.mark.asyncio
async def test_handle_decline_callback(monkeypatch):
    # Simulate admin declining
    cb = DummyCallback(admin_id=2)
    mb = []
    cb.bot.send_message = lambda chat_id, text: mb.append((chat_id, text))
    # Call handler directly
    await ga_mod.handle_decline_callback(cb, SimpleNamespace(action="decline", user_id="88"))
    assert (88, "Вам отказано в доступе") in mb
    assert "Доступ отклонён." in cb.replies
