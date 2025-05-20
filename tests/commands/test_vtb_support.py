import pytest
from types import SimpleNamespace

import bot.commands.vtb_support as support_mod

# --- Подготовка dummy-объектов ---

class DummyEvent(SimpleNamespace):
    def __init__(self):
        super().__init__()
        self.answers = []

    async def answer(self, text):
        self.answers.append(text)

async def dummy_handler(event, data):
    # простой «handler», который подтверждает факт вызова
    event.answers.append("handler_called")
    return "handler_ok"

class DummyMessage(SimpleNamespace):
    def __init__(self):
        super().__init__()
        self.answers = []
        self.from_user = SimpleNamespace(id=123)
        self.chat = SimpleNamespace(id=456)

    async def answer(self, text):
        self.answers.append(text)

class DummyDispatcher:
    def __init__(self):
        self.routers = []

    def include_router(self, router):
        self.routers.append(router)

# --- Тесты middleware ---

@pytest.mark.asyncio
async def test_feature_flag_middleware_disabled(monkeypatch):
    # Флаг выключен -> middleware перехватывает и отвечает сообщением
    monkeypatch.setattr(support_mod, "VTB_SUPPORT_ENABLE", False)
    ev = DummyEvent()
    result = await support_mod.feature_flag_middleware(dummy_handler, ev, {})
    assert ev.answers == ["Команда временно отключена."]
    assert result is None

@pytest.mark.asyncio
async def test_feature_flag_middleware_enabled(monkeypatch):
    # Флаг включен -> middleware пропускает к handler
    monkeypatch.setattr(support_mod, "VTB_SUPPORT_ENABLE", True)
    ev = DummyEvent()
    result = await support_mod.feature_flag_middleware(dummy_handler, ev, {})
    assert ev.answers == ["handler_called"]
    assert result == "handler_ok"

# --- Тесты самого handler'а ---

@pytest.mark.asyncio
async def test_handle_vtb_support_sends_phone(monkeypatch):
    # Убедимся, что при включённом флаге handler отправляет номер
    monkeypatch.setattr(support_mod, "VTB_SUPPORT_ENABLE", True)
    msg = DummyMessage()
    await support_mod.handle_vtb_support(msg)
    assert msg.answers == [support_mod.PHONE_SUPPORT_TEXT]

# --- Тест регистрации роутера ---

def test_register_vtb_support_handler_includes_router():
    dp = DummyDispatcher()
    support_mod.register(dp)
    assert support_mod.router in dp.routers
