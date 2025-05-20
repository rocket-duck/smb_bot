import pytest
from types import SimpleNamespace

import bot.commands.start as start_mod

class DummyMessage(SimpleNamespace):
    def __init__(self, from_user, chat):
        super().__init__()
        self.from_user = from_user
        self.chat = chat
        self.answers = []

    async def answer(self, text):
        self.answers.append(text)

class DummyDispatcher:
    def __init__(self):
        self.included = []

    def include_router(self, router):
        self.included.append(router)

@pytest.mark.asyncio
async def test_handle_start_sends_greeting(monkeypatch):
    # Prepare dummy message with from_user and chat attributes
    user = SimpleNamespace(id=123)
    chat = SimpleNamespace(id=456)
    msg = DummyMessage(from_user=user, chat=chat)

    # Call the handler
    await start_mod.handle_start(msg)

    # Check that the greeting was sent
    assert msg.answers == [start_mod.GREETING_TEXT]

def test_register_includes_router():
    dp = DummyDispatcher()
    # Call the registration function
    start_mod.register(dp)

    # Ensure the start router was included
    assert start_mod.router in dp.included
