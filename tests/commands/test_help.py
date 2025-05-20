# Stub aiogram.filters.Command to a no-op decorator to avoid registration errors
import aiogram.filters
aiogram.filters.Command = lambda *args, **kwargs: (lambda func: func)
import pytest
from types import SimpleNamespace
import bot.commands.help as help_mod
from html import escape

# Dummy message for testing
class DummyMessage:
    def __init__(self, user_id=1, chat_id=2, chat_type="group"):
        self.from_user = SimpleNamespace(id=user_id)
        self.chat = SimpleNamespace(id=chat_id, type=chat_type)
        self.answers = []

    async def answer(self, text):
        self.answers.append(text)

@pytest.mark.asyncio
async def test_no_commands_available(monkeypatch):
    # No commands returned => generic message
    monkeypatch.setattr(help_mod, "_cached_get_command_defs", lambda user_is_admin: [])
    monkeypatch.setattr(help_mod, "is_user_admin", lambda uid: False)
    msg = DummyMessage()
    await help_mod.handle_help(msg)
    assert msg.answers == ["Нет доступных команд для вашего чата."]

@pytest.mark.asyncio
async def test_private_and_group_filtering(monkeypatch):
    # Define two commands, one for private, one for group
    defs = [
        SimpleNamespace(command="c1", description="D1", private_chat=True, group_chat=False, visible_in_help=True),
        SimpleNamespace(command="c2", description="D2", private_chat=False, group_chat=True, visible_in_help=True)
    ]
    monkeypatch.setattr(help_mod, "_cached_get_command_defs", lambda user_is_admin: defs)
    monkeypatch.setattr(help_mod, "is_user_admin", lambda uid: False)

    # Private chat
    msg_priv = DummyMessage(chat_type="private")
    await help_mod.handle_help(msg_priv)
    assert msg_priv.answers == ["Привет! Вот список доступных команд:\n\n/c1 — D1"]

    # Group chat
    msg_group = DummyMessage(chat_type="group")
    await help_mod.handle_help(msg_group)
    assert msg_group.answers == ["Привет! Вот список доступных команд:\n\n/c2 — D2"]

@pytest.mark.asyncio
async def test_visible_in_help_filtering(monkeypatch):
    # One command not visible
    defs = [
        SimpleNamespace(command="c1", description="D1", private_chat=True, group_chat=True, visible_in_help=False),
        SimpleNamespace(command="c2", description="D2", private_chat=True, group_chat=True, visible_in_help=True)
    ]
    monkeypatch.setattr(help_mod, "_cached_get_command_defs", lambda user_is_admin: defs)
    monkeypatch.setattr(help_mod, "is_user_admin", lambda uid: False)
    msg = DummyMessage()
    await help_mod.handle_help(msg)
    assert msg.answers == ["Привет! Вот список доступных команд:\n\n/c2 — D2"]

@pytest.mark.asyncio
async def test_admin_commands(monkeypatch):
    # One admin-only command
    defs = [
        SimpleNamespace(command="admincmd", description="Admin only", private_chat=True, group_chat=True, visible_in_help=True, is_admin=True),
        SimpleNamespace(command="usercmd", description="User", private_chat=True, group_chat=True, visible_in_help=True, is_admin=False)
    ]
    # When not admin
    monkeypatch.setattr(help_mod, "_cached_get_command_defs", lambda user_is_admin: defs if user_is_admin else [defs[0]])
    monkeypatch.setattr(help_mod, "is_user_admin", lambda uid: False)
    msg = DummyMessage()
    await help_mod.handle_help(msg)
    # Only admin-only in defs for non-admin? But get_command_defs filters is_admin => maintaining structure:
    # Instead, adjust: if not admin, get_command_defs returns only non-admin entries:
    monkeypatch.setattr(help_mod, "_cached_get_command_defs", lambda user_is_admin: [defs[1]] if not user_is_admin else defs)
    monkeypatch.setattr(help_mod, "is_user_admin", lambda uid: False)
    msg = DummyMessage()
    await help_mod.handle_help(msg)
    assert msg.answers == ["Привет! Вот список доступных команд:\n\n/usercmd — User"]

    # When admin
    monkeypatch.setattr(help_mod, "is_user_admin", lambda uid: True)
    monkeypatch.setattr(help_mod, "_cached_get_command_defs", lambda user_is_admin: defs)
    msg_admin = DummyMessage()
    await help_mod.handle_help(msg_admin)
    assert msg_admin.answers == ["Привет! Вот список доступных команд:\n\n/admincmd — Admin only\n/usercmd — User"]

@pytest.mark.asyncio
async def test_html_escaping(monkeypatch):
    # Test HTML escaping in descriptions
    defs = [
        SimpleNamespace(command="c1", description="<b>bold", private_chat=True, group_chat=True, visible_in_help=True)
    ]
    monkeypatch.setattr(help_mod, "_cached_get_command_defs", lambda user_is_admin: defs)
    monkeypatch.setattr(help_mod, "is_user_admin", lambda uid: False)
    msg = DummyMessage()
    await help_mod.handle_help(msg)
    expected = f"/c1 — {escape('<b>bold')}"
    assert msg.answers == [f"Привет! Вот список доступных команд:\n\n{expected}"]