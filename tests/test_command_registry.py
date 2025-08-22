import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from bot.utils import command_registry


@pytest.mark.asyncio
async def test_command_registered_and_exec():
    command_registry.COMMAND_REGISTRY.clear()
    called = {"value": False}

    async def handler(message):
        called["value"] = True
        await message.answer("ok")

    message = SimpleNamespace(from_user=SimpleNamespace(id=1), answer=AsyncMock())
    decorated = command_registry.command("test")(handler)

    assert command_registry.COMMAND_REGISTRY[-1]["name"] == "test"
    await decorated(message)
    assert called["value"] is True
    message.answer.assert_awaited_once_with("ok")


@pytest.mark.asyncio
async def test_command_flag_false():
    command_registry.COMMAND_REGISTRY.clear()
    called = {"value": False}

    async def handler(message):
        called["value"] = True

    message = SimpleNamespace(from_user=SimpleNamespace(id=1), answer=AsyncMock())
    decorated = command_registry.command("test", flag=False)(handler)

    await decorated(message)
    assert called["value"] is False
    message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_command_admin_only(monkeypatch):
    command_registry.COMMAND_REGISTRY.clear()
    called = {"value": False}

    async def handler(message):
        called["value"] = True

    message = SimpleNamespace(from_user=SimpleNamespace(id=1), answer=AsyncMock())
    monkeypatch.setattr(
        command_registry, "is_user_admin_db", AsyncMock(return_value=False)
    )
    decorated = command_registry.command("test", admin_only=True)(handler)

    await decorated(message)
    assert called["value"] is False
    message.answer.assert_awaited_once_with(
        "У вас нет прав для использования этой команды.\n"
        "Запросить права вы можете командой /get_access"
    )
