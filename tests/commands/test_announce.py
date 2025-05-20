import pytest
from types import SimpleNamespace

from bot.commands.announce import prepare_announce, send_announce_to_chat

class DummyBot:
    def __init__(self):
        self.sent = []

    async def send_message(self, chat_id, text):
        self.sent.append((chat_id, text))

class DummyReply:
    def __init__(self):
        self.forwarded_to = []

    async def forward(self, chat_id):
        self.forwarded_to.append(chat_id)

@pytest.mark.asyncio
async def test_prepare_announce_with_reply_and_text():
    reply = DummyReply()
    message = SimpleNamespace(text="/announce hello world", reply_to_message=reply)
    result = await prepare_announce(message)
    assert result == ("hello world", reply)

@pytest.mark.asyncio
async def test_prepare_announce_with_reply_no_text():
    reply = DummyReply()
    message = SimpleNamespace(text="/announce    ", reply_to_message=reply)
    result = await prepare_announce(message)
    assert result == (None, reply)

@pytest.mark.asyncio
async def test_prepare_announce_without_reply_with_args():
    message = SimpleNamespace(text="/announce TestArg", reply_to_message=None)
    result = await prepare_announce(message)
    assert result == ("TestArg", None)

@pytest.mark.asyncio
async def test_prepare_announce_without_reply_plain_text():
    message = SimpleNamespace(text="Plain text", reply_to_message=None)
    result = await prepare_announce(message)
    assert result == ("Plain text", None)

@pytest.mark.asyncio
async def test_prepare_announce_without_reply_empty_text():
    message = SimpleNamespace(text="", reply_to_message=None)
    result = await prepare_announce(message)
    assert result == (None, None)

@pytest.mark.asyncio
async def test_send_announce_to_chat_text_and_forward():
    bot = DummyBot()
    reply = DummyReply()
    message = SimpleNamespace(bot=bot)
    chat = {"id": 10, "title": "Chat10"}
    await send_announce_to_chat(chat, message, "Announcement", reply)
    assert bot.sent == [(10, "Announcement")]
    assert reply.forwarded_to == [10]

@pytest.mark.asyncio
async def test_send_announce_to_chat_only_text():
    bot = DummyBot()
    message = SimpleNamespace(bot=bot)
    chat = {"id": 20, "title": "Chat20"}
    await send_announce_to_chat(chat, message, "OnlyText", None)
    assert bot.sent == [(20, "OnlyText")]

@pytest.mark.asyncio
async def test_send_announce_to_chat_only_forward():
    bot = DummyBot()
    reply = DummyReply()
    message = SimpleNamespace(bot=bot)
    chat = {"id": 30, "title": "Chat30"}
    await send_announce_to_chat(chat, message, None, reply)
    assert reply.forwarded_to == [30]
    assert bot.sent == []