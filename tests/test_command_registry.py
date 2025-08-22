import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from aiogram.filters import Command

from bot.utils import command_registry


@pytest.mark.asyncio
async def test_command_registered_and_exec():
    command_registry.COMMAND_REGISTRY.clear()
    called = {"value": False}

    async def handler(message):
        called["value"] = True
        await message.answer("ok")

    message = SimpleNamespace(
        from_user=SimpleNamespace(id=1), answer=AsyncMock()
    )
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

    message = SimpleNamespace(
        from_user=SimpleNamespace(id=1), answer=AsyncMock()
    )
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

    message = SimpleNamespace(
        from_user=SimpleNamespace(id=1), answer=AsyncMock()
    )
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


def test_command_router_registration():
    mock_router = MagicMock()
    mock_router.message.register = MagicMock()

    start_len = len(command_registry.COMMAND_REGISTRY)

    @command_registry.command("test", router=mock_router)
    async def sample_handler(message):
        pass

    mock_router.message.register.assert_called_once()
    args, kwargs = mock_router.message.register.call_args
    assert args[0] is sample_handler
    command_filter = args[1]
    assert isinstance(command_filter, Command)
    assert command_filter.commands == ("test",)

    assert command_registry.COMMAND_REGISTRY[-1]["router"] is mock_router
    assert len(command_registry.COMMAND_REGISTRY) == start_len + 1

    command_registry.COMMAND_REGISTRY[:] = command_registry.COMMAND_REGISTRY[
        :start_len
    ]
