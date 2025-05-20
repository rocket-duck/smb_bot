import pytest
from types import SimpleNamespace
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

import bot.commands.docs as docs_module
from bot.services.docs_service import DocsServiceDisabled, EmptyDocsMenu

class DummyState(FSMContext):
    def __init__(self):
        # no real state required; track calls
        self.cleared = False
        self.updated = {}

    async def clear(self):
        self.cleared = True

    async def update_data(self, **data):
        self.updated.update(data)

class DummyMessage:
    def __init__(self, user=None):
        self.from_user = user
        self.answers = []
        self.replies = []

    async def answer(self, text, reply_markup=None):
        self.answers.append((text, reply_markup))

    async def reply(self, text):
        self.replies.append(text)

@pytest.mark.asyncio
async def test_handle_docs_success(monkeypatch):
    # Prepare dummy menu and text
    dummy_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="A", callback_data="a")]])
    dummy_text = "Main menu text"
    # Stub get_docs_menu
    monkeypatch.setattr(docs_module, 'get_docs_menu',
                        lambda user_id: (dummy_menu, dummy_text))
    user = SimpleNamespace(id=1, username="u", full_name="FN")
    msg = DummyMessage(user=user)
    state = DummyState()
    await docs_module.handle_docs(msg, state)
    # Ensure state cleared and data updated
    assert state.cleared is True
    assert state.updated.get('main_menu_text') == dummy_text
    # Ensure answer called with correct text and menu
    assert msg.answers == [(dummy_text, dummy_menu)]

@pytest.mark.asyncio
async def test_handle_docs_disabled(monkeypatch):
    monkeypatch.setattr(docs_module, 'get_docs_menu',
                        lambda user_id: (_ for _ in ()).throw(DocsServiceDisabled()))
    user = SimpleNamespace(id=2, username="u2", full_name="FN2")
    msg = DummyMessage(user=user)
    state = DummyState()
    await docs_module.handle_docs(msg, state)
    # Should clear and send disabled message
    assert state.cleared is True
    assert msg.answers == [("Команда временно отключена.", None)]

@pytest.mark.asyncio
async def test_handle_docs_empty(monkeypatch):
    monkeypatch.setattr(docs_module, 'get_docs_menu',
                        lambda user_id: (_ for _ in ()).throw(EmptyDocsMenu()))
    user = SimpleNamespace(id=3, username="u3", full_name="FN3")
    msg = DummyMessage(user=user)
    state = DummyState()
    await docs_module.handle_docs(msg, state)
    assert state.cleared is True
    assert msg.answers == [("Меню временно недоступно. Обратитесь к администратору.", None)]

@pytest.mark.asyncio
async def test_handle_docs_exception(monkeypatch):
    monkeypatch.setattr(docs_module, 'get_docs_menu',
                        lambda user_id: (_ for _ in ()).throw(Exception("fail")))
    user = SimpleNamespace(id=4, username="u4", full_name="FN4")
    msg = DummyMessage(user=user)
    state = DummyState()
    await docs_module.handle_docs(msg, state)
    # Generic exception should trigger generic error reply
    assert msg.replies == ["Произошла внутренняя ошибка. Попробуйте позже."]

@pytest.mark.asyncio
async def test_handle_docs_no_user(monkeypatch):
    # Simulate missing from_user or id
    msg = DummyMessage(user=None)
    state = DummyState()
    # Stub clear to avoid errors
    await docs_module.handle_docs(msg, state)
    # Should prompt error about user id
    assert msg.answers == [("Ошибка: не удалось определить ваш идентификатор.", None)]
@pytest.mark.asyncio
async def test_handle_docs_state_clear_error(monkeypatch):
    """
    Simulate failure in state.clear(): handler should catch and reply with generic error.
    """
    # Stub get_docs_menu to normal behavior
    dummy_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="A", callback_data="a")]])
    dummy_text = "Main menu text"
    monkeypatch.setattr(docs_module, "get_docs_menu",
                        lambda user_id: (dummy_menu, dummy_text))

    # Create a state whose clear() throws
    class ErrorState(DummyState):
        async def clear(self):
            raise RuntimeError("clear failed")

    user = SimpleNamespace(id=5, username="u5", full_name="FN5")
    msg = DummyMessage(user=user)
    state = ErrorState()

    await docs_module.handle_docs(msg, state)
    # Should catch clear exception and reply with generic error
    assert msg.replies and "Произошла внутренняя ошибка." in msg.replies[0]

@pytest.mark.asyncio
async def test_handle_docs_state_update_error(monkeypatch):
    """
    Simulate failure in state.update_data(): handler should catch and reply with generic error.
    """
    # Stub get_docs_menu to normal behavior
    dummy_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="A", callback_data="a")]])
    dummy_text = "Main menu text"
    monkeypatch.setattr(docs_module, "get_docs_menu",
                        lambda user_id: (dummy_menu, dummy_text))

    # Create a state whose update_data() throws
    class ErrorState2(DummyState):
        async def update_data(self, **data):
            raise RuntimeError("update_data failed")

    user = SimpleNamespace(id=6, username="u6", full_name="FN6")
    msg = DummyMessage(user=user)
    state = ErrorState2()

    await docs_module.handle_docs(msg, state)
    # Should catch update_data exception and reply with generic error
    assert msg.replies and "Произошла внутренняя ошибка." in msg.replies[0]