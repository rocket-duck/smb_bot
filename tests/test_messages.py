import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from aiogram.types import Message, Chat, User
from bot.messages.messages import handle_message
from bot.services.message_service import message_service
from bot.services.message_parse_service import parse_message_service


@pytest.fixture
def mock_message():
    msg = MagicMock(spec=Message)
    msg.text = "test message"
    msg.chat = Chat(id=123, type="private")
    msg.from_user = User(id=456, first_name="Test", is_bot=False)
    msg.answer = AsyncMock()
    return msg


@pytest.mark.asyncio
async def test_handle_message_bot_tag_detected(mock_message):
    with patch("bot.messages.messages.handle_bot_tag", new_callable=AsyncMock) as mock_bot_tag, \
            patch("bot.messages.messages.handle_fan_triggers", new_callable=AsyncMock) as mock_fan_triggers:
        mock_bot_tag.return_value = True

        await handle_message(mock_message)

        mock_bot_tag.assert_awaited_once()
        mock_fan_triggers.assert_not_awaited()


@pytest.mark.asyncio
async def test_handle_message_process_links(mock_message):
    with patch("bot.messages.messages.handle_bot_tag", new_callable=AsyncMock, return_value=False), \
            patch("bot.messages.messages.handle_fan_triggers", new_callable=AsyncMock), \
            patch.object(parse_message_service, "find_links", return_value=[("Test Link", "http://test.com")]), \
            patch.object(message_service, "process_results", new_callable=AsyncMock) as mock_process_results:
        await handle_message(mock_message)

        mock_process_results.assert_awaited_once_with(mock_message, [("Test Link", "http://test.com")])


@pytest.mark.asyncio
async def test_handle_message_fan_triggers(mock_message):
    with patch("bot.messages.messages.handle_bot_tag", new_callable=AsyncMock, return_value=False), \
            patch("bot.messages.messages.handle_fan_triggers", new_callable=AsyncMock) as mock_fan_triggers, \
            patch.object(parse_message_service, "find_links", return_value=[]), \
            patch.object(message_service, "process_results", new_callable=AsyncMock):
        await handle_message(mock_message)

        mock_fan_triggers.assert_awaited_once_with(mock_message)


@pytest.mark.asyncio
async def test_error_middleware():
    handler_mock = AsyncMock(side_effect=Exception("Test exception"))
    event_mock = AsyncMock(spec=Message)
    event_mock.answer = AsyncMock()

    from bot.messages.messages import error_middleware

    await error_middleware(handler_mock, event_mock, {})

    event_mock.answer.assert_awaited_once_with("Извините, произошла внутренняя ошибка. Попробуйте позже.")
