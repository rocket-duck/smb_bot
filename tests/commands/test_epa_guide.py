import pytest
from types import SimpleNamespace
import bot.commands.epa_guide as epa_mod


class DummyMessage:
    def __init__(self):
        # ответ через answer и через reply
        self.answers = []
        self.replies = []
        self.from_user = SimpleNamespace(id=1)
        self.chat = SimpleNamespace(id=1, type="group")
    async def answer(self, text):
        self.answers.append(text)
    async def reply(self, text):
        self.replies.append(text)


@pytest.mark.asyncio
async def test_handle_epa_guide_enabled(monkeypatch):
    # Флаг включен — поведение по умолчанию
    monkeypatch.setattr(epa_mod, "GET_EPA_GUIDE_ENABLE", True)
    msg = DummyMessage()
    await epa_mod.handle_epa_guide(msg)
    # проверяем, что отправился корректный текст с двумя ссылками
    assert len(msg.answers) == 1
    assert "ЕПА-3" in msg.answers[0] and "ЕПА-10" in msg.answers[0]


@pytest.mark.asyncio
async def test_handle_epa_guide_exception(monkeypatch):
    # Заменяем логику хендлера на бросающую RuntimeError
    async def fake_inner(message):
        raise RuntimeError("oops")
    # Мокаем обёртку
    monkeypatch.setattr(
        epa_mod,
        "handle_epa_guide",
        epa_mod.catch_exceptions(fake_inner)
    )
    msg = DummyMessage()
    await epa_mod.handle_epa_guide(msg)
    # Должен сработать catch_exceptions и вызвать reply
    assert msg.answers == []
    assert msg.replies == ["Произошла внутренняя ошибка. Попробуйте позже."]
