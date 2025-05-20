import pytest
from types import SimpleNamespace

import bot.commands.epa_contacts as epa_mod

# Dummy message object
class DummyMessage:
    def __init__(self):
        self.answers = []
        self.replies = []
        self.from_user = SimpleNamespace(id=123)

    async def answer(self, text):
        self.answers.append(text)

    async def reply(self, text):
        self.replies.append(text)

@pytest.mark.asyncio
async def test_handle_epa_contacts_success(monkeypatch):
    """
    When GET_EPA_CONTACTS_ENABLE=True (default), handler should send the EPA contacts link.
    """
    msg = DummyMessage()
    # Ensure feature flag enabled
    monkeypatch.setattr(epa_mod, "GET_EPA_CONTACTS_ENABLE", True)
    await epa_mod.handle_epa_contacts(msg)
    assert msg.answers == [
        "Контакты ЕПА для связи: https://sfera.inno.local/knowledge/pages?id=1524162"
    ]
    assert msg.replies == []

@pytest.mark.asyncio
async def test_handle_epa_contacts_exception(monkeypatch):
    """
    Simulate an unexpected exception inside the handler: wrapper should catch and reply with generic error.
    """
    # Replace the inner function to always raise
    async def fake_inner(message):
        raise RuntimeError("oops")
    # Replace the handler with a wrapped fake that always raises
    monkeypatch.setattr(
        epa_mod,
        "handle_epa_contacts",
        epa_mod.catch_exceptions(fake_inner)
    )

    msg = DummyMessage()
    await epa_mod.handle_epa_contacts(msg)
    assert msg.answers == []
    assert msg.replies == ["Произошла внутренняя ошибка. Попробуйте позже."]