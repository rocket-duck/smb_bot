from unittest.mock import MagicMock

from aiogram.filters import Command

from bot.utils.command_registry import COMMAND_REGISTRY, command


def test_command_router_registration():
    mock_router = MagicMock()
    mock_router.message.register = MagicMock()

    start_len = len(COMMAND_REGISTRY)

    @command("test", router=mock_router)
    async def sample_handler(message):
        pass

    mock_router.message.register.assert_called_once()
    args, kwargs = mock_router.message.register.call_args
    assert args[0] is sample_handler
    command_filter = args[1]
    assert isinstance(command_filter, Command)
    assert command_filter.commands == ("test",)

    assert COMMAND_REGISTRY[-1]["router"] is mock_router
    assert len(COMMAND_REGISTRY) == start_len + 1

    COMMAND_REGISTRY[:] = COMMAND_REGISTRY[:start_len]
