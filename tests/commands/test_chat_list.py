import pytest
import asyncio
from types import SimpleNamespace

import bot.commands.chat_list as chat_list_mod
from bot.commands.chat_list import handle_chat_list

# Заглушка для message.answer
class DummyMessage:
    def __init__(self, from_user, chat=None):
        self.from_user = from_user
        # Default to a group chat if not provided
        from types import SimpleNamespace
        self.chat = chat or SimpleNamespace(id=1, type="group")
        self.answers = []

    async def answer(self, text):
        self.answers.append(text)

# Заглушка для пользователя
class DummyUser:
    def __init__(self, user_id):
        self.id = user_id

@pytest.mark.asyncio
async def test_handle_chat_list_empty_list(monkeypatch):
    # Админ, но нет чатов
    monkeypatch.setattr(chat_list_mod, 'is_user_admin', lambda uid: True)
    monkeypatch.setattr(chat_list_mod, 'get_all_chats', lambda: [])
    msg = DummyMessage(from_user=DummyUser(3))
    await handle_chat_list(msg)
    assert msg.answers == ["Список чатов пуст."]

@pytest.mark.asyncio
async def test_handle_chat_list_with_chats(monkeypatch):
    # Админ, есть несколько чатов
    monkeypatch.setattr(chat_list_mod, 'is_user_admin', lambda uid: True)
    sample = [
        {'chat_id': 10, 'title': 'One', 'deleted': False},
        {'chat_id': 20, 'title': None,  'deleted': True},
    ]
    monkeypatch.setattr(chat_list_mod, 'get_all_chats', lambda: sample)
    msg = DummyMessage(from_user=DummyUser(4))
    await handle_chat_list(msg)
    # Первый элемент – заголовок
    assert msg.answers, "Должны быть ответы"
    lines = msg.answers[0].splitlines()
    assert lines[0] == "Список известных чатов:"
    # Проверяем обработку названий и статуса
    assert "One (ID: 10) - активен" in lines[1]
    assert "Без названия (ID: 20) - удалён" in lines[2]

@pytest.mark.asyncio
async def test_handle_chat_list_unexpected_error(monkeypatch):
    # Админ, get_all_chats бросает
    monkeypatch.setattr(chat_list_mod, 'is_user_admin', lambda uid: True)
    monkeypatch.setattr(chat_list_mod, 'get_all_chats', lambda: (_ for _ in ()).throw(ValueError("oops")))
    msg = DummyMessage(from_user=DummyUser(5))
    await handle_chat_list(msg)
    assert msg.answers == ["Произошла внутренняя ошибка."]
