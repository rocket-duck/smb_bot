import pytest
from types import SimpleNamespace

import bot.services.best_qa_service as best_qa_service
import bot.commands.best_qa as best_qa_mod
from bot.commands.best_qa import handle_best_qa


@pytest.mark.asyncio
async def test_handle_best_qa_disabled(monkeypatch):
    # Command flag disabled
    monkeypatch.setattr(best_qa_mod, "BEST_QA_ENABLE", False)
    msg = SimpleNamespace(chat=SimpleNamespace(id=1, type="group", title="Chat"))
    # Capture answers
    msg.answers = []
    async def answer(text, parse_mode=None):
        msg.answers.append((text, parse_mode))
    msg.answer = answer

    await handle_best_qa(msg)
    assert msg.answers == [("Команда временно отключена.", None)]

@pytest.mark.asyncio
async def test_handle_best_qa_private_chat(monkeypatch):
    monkeypatch.setattr(best_qa_mod, "BEST_QA_ENABLE", True)
    msg = SimpleNamespace(chat=SimpleNamespace(id=2, type="private", title=""))
    msg.answers = []
    async def answer(text, parse_mode=None):
        msg.answers.append((text, parse_mode))
    msg.answer = answer

    await handle_best_qa(msg)
    assert msg.answers == [("Эта команда доступна только в групповых чатах.", None)]

@pytest.mark.asyncio
async def test_handle_best_qa_already_chosen(monkeypatch):
    monkeypatch.setattr(best_qa_mod, "BEST_QA_ENABLE", True)
    # Stub select_best_qa to raise AlreadyChosenToday
    class DummyLast:
        winner_user_id = "99"
        winner_full_name = "Tester"
    async def fake_select(chat_id, chat_title):
        raise best_qa_service.AlreadyChosenToday(DummyLast())
    monkeypatch.setattr(best_qa_mod, "select_best_qa", fake_select)
    # Stub format_winner_mention
    monkeypatch.setattr(best_qa_mod, "format_winner_mention", lambda uid, name: f"<@{uid}>")

    msg = SimpleNamespace(chat=SimpleNamespace(id=3, type="group", title="G"))
    msg.answers = []
    async def answer(text, parse_mode=None):
        msg.answers.append((text, parse_mode))
    msg.answer = answer

    await handle_best_qa(msg)
    expected = "Сегодня лучший тестировщик уже выбран: <@99> 🎉"
    assert msg.answers == [(expected, "HTML")]

@pytest.mark.asyncio
async def test_handle_best_qa_no_participants(monkeypatch):
    monkeypatch.setattr(best_qa_mod, "BEST_QA_ENABLE", True)
    # Stub select_best_qa to raise NoParticipants
    async def fake_select(chat_id, chat_title):
        raise best_qa_service.NoParticipants()
    monkeypatch.setattr(best_qa_mod, "select_best_qa", fake_select)

    msg = SimpleNamespace(chat=SimpleNamespace(id=4, type="group", title="G"))
    msg.answers = []
    async def answer(text, parse_mode=None):
        msg.answers.append((text, parse_mode))
    msg.answer = answer

    await handle_best_qa(msg)
    assert msg.answers == [("Не нашёл участников для выбора.", None)]

@pytest.mark.asyncio
async def test_handle_best_qa_success(monkeypatch):
    monkeypatch.setattr(best_qa_mod, "BEST_QA_ENABLE", True)
    # Stub select_best_qa to return a mention
    async def fake_select(chat_id, chat_title):
        return "<@123>"
    monkeypatch.setattr(best_qa_mod, "select_best_qa", fake_select)

    msg = SimpleNamespace(chat=SimpleNamespace(id=5, type="group", title="Title"))
    msg.answers = []
    async def answer(text, parse_mode=None):
        msg.answers.append((text, parse_mode))
    msg.answer = answer

    await handle_best_qa(msg)
    assert msg.answers == [("Сегодня лучший тестировщик <@123> 🎉", "HTML")]

@pytest.mark.asyncio
async def test_handle_best_qa_unexpected_error(monkeypatch):
    monkeypatch.setattr(best_qa_mod, "BEST_QA_ENABLE", True)
    # Stub select_best_qa to raise generic exception
    async def fake_select(chat_id, chat_title):
        raise RuntimeError("oops")
    monkeypatch.setattr(best_qa_mod, "select_best_qa", fake_select)

    msg = SimpleNamespace(chat=SimpleNamespace(id=6, type="group", title="T"))
    msg.replies = []
    async def reply(text):
        msg.replies.append(text)
    msg.reply = reply

    await handle_best_qa(msg)
    assert msg.replies == ["Произошла ошибка при выборе лучшего тестировщика."]