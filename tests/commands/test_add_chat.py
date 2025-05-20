import pytest
from types import SimpleNamespace

import bot.commands.add_chat as add_chat_mod
from bot.commands.add_chat import handle_add_chat
from bot.config.flags import ADD_CHAT_ENABLE

# Dummy message for testing
class DummyMessage:
    def __init__(self, chat_id=1, title="Title", user_id=1, username="user", full_name="User", chat_type="group"):
        self.chat = SimpleNamespace(id=chat_id, title=title, type=chat_type)
        self.from_user = SimpleNamespace(id=user_id, username=username, full_name=full_name)
        self.deleted = False
        self.deleted_calls = 0

    async def delete(self):
        self.deleted_calls += 1
        self.deleted = True

# Stub add_chat to capture calls
@pytest.fixture(autouse=True)
def stub_add_chat(monkeypatch):
    calls = []
    def fake_add_chat(cid, title, added_by):
        calls.append((cid, title, added_by))
    monkeypatch.setattr(add_chat_mod, "add_chat", fake_add_chat)
    return calls

@pytest.mark.asyncio
async def test_handle_add_chat_disabled(stub_add_chat, monkeypatch):
    # Command disabled: should do nothing
    monkeypatch.setattr(add_chat_mod, "ADD_CHAT_ENABLE", False)
    monkeypatch.setattr(add_chat_mod, "is_user_admin", lambda uid: True)
    msg = DummyMessage()
    await handle_add_chat(msg)
    assert msg.deleted
    assert stub_add_chat == []

@pytest.mark.asyncio
async def test_handle_add_chat_not_admin(stub_add_chat, monkeypatch):
    # Enabled but not admin: should do nothing
    monkeypatch.setattr(add_chat_mod, "ADD_CHAT_ENABLE", True)
    monkeypatch.setattr(add_chat_mod, "is_user_admin", lambda uid: False)
    msg = DummyMessage()
    await handle_add_chat(msg)
    assert msg.deleted
    assert stub_add_chat == []

@pytest.mark.asyncio
async def test_handle_add_chat_success(stub_add_chat, monkeypatch):
    # Enabled and admin: should delete and add
    monkeypatch.setattr(add_chat_mod, "ADD_CHAT_ENABLE", True)
    monkeypatch.setattr(add_chat_mod, "is_user_admin", lambda uid: True)
    msg = DummyMessage(chat_id=10, title="ChatTitle", user_id=2, username="user2", full_name="User Two")
    await handle_add_chat(msg)
    assert msg.deleted
    assert stub_add_chat == [(10, "ChatTitle", "user2")]

@pytest.mark.asyncio
async def test_handle_add_chat_exception_logged(stub_add_chat, monkeypatch, caplog):
    # Enabled and admin, but add_chat raises: should still delete and log
    monkeypatch.setattr(add_chat_mod, "ADD_CHAT_ENABLE", True)
    monkeypatch.setattr(add_chat_mod, "is_user_admin", lambda uid: True)
    def raise_add(cid, title, added_by):
        raise RuntimeError("fail")
    monkeypatch.setattr(add_chat_mod, "add_chat", raise_add)
    caplog.set_level("ERROR")
    msg = DummyMessage()
    await handle_add_chat(msg)
    assert msg.deleted
    assert "Ошибка при добавлении чата" in caplog.text
