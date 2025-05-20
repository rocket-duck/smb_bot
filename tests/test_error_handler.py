import pytest
from bot.utils.handlers import global_error_handler

class DummyMessage:
    def __init__(self):
        self.replies = []
    async def reply(self, text):
        self.replies.append(text)

class DummyUpdate:
    def __init__(self):
        self.message = DummyMessage()

@pytest.mark.asyncio
async def test_global_error_handler_logs_and_replies(caplog):
    update = DummyUpdate()
    caplog.set_level("ERROR")
    handled = await global_error_handler(update, Exception("oops"))
    # Проверяем, что функция вернула True (чтобы Aiogram не продолжал)
    assert handled is True
    # Лог должен содержать текст ошибки
    assert "oops" in caplog.text
    # Пользователю был отправлен ответ-извинение
    assert update.message.replies == ["Извините, что-то пошло не так. Попробуйте позже."]

import pytest
from bot.utils.handlers import global_error_handler

class DummyMessage:
    def __init__(self):
        self.replies = []

    async def reply(self, text):
        self.replies.append(text)

class DummyUpdate:
    def __init__(self):
        self.message = DummyMessage()

@pytest.mark.asyncio
async def test_global_error_handler_logs_and_replies(caplog):
    update = DummyUpdate()
    caplog.set_level("ERROR")
    handled = await global_error_handler(update, Exception("oops"))
    assert handled is True
    assert "oops" in caplog.text
    assert update.message.replies == ["Извините, что-то пошло не так. Попробуйте позже."]