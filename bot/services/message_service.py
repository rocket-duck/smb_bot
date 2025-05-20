import logging
import asyncio
from typing import List, Tuple

from aiogram.types import Message
from bot.config.flags import TIMEOUT_RESPONSES_ENABLE, TIMEOUT_MINUTES
from bot.services.recent_links_service import RecentLinksService
from bot.messages.formatter import format_response

logger = logging.getLogger(__name__)

class MessageService:
    """
    Service for processing link results and timing out recently sent links.
    """
    def __init__(self) -> None:
        self.link_service = RecentLinksService(ttl_minutes=TIMEOUT_MINUTES)

    async def process_results(self, message: Message, results: List[Tuple[str, str]]) -> None:
        """
        Filters, formats, and sends link results to the user.
        Then schedules removal of those links from cache after TTL.
        """
        # Filter out recently sent links if enabled
        filtered = (
            self.link_service.filter(message.chat.id, results)
            if TIMEOUT_RESPONSES_ENABLE
            else results
        )

        if not filtered:
            logger.debug("No new links to send for chat %s.", message.chat.id)
            return

        # Format and send the response
        response_text = format_response(filtered)
        logger.debug("Sending links response to chat %s: %s", message.chat.id, response_text)
        await message.answer(response_text)

        # Schedule removal from recent cache after TTL
        if TIMEOUT_RESPONSES_ENABLE:
            for _, url in filtered:
                asyncio.create_task(self._remove_link_after_timeout(message.chat.id, url))

    async def _remove_link_after_timeout(self, chat_id: int, url: str) -> None:
        """
        Wait for TTL, then clear the link from cache for the given chat.
        """
        await asyncio.sleep(TIMEOUT_MINUTES * 60)
        removed = self.link_service.cache.get(chat_id, {}).pop(url, None)
        if removed:
            logger.debug("Removed link '%s' from cache for chat %s", url, chat_id)


# Export default instance for use in handlers
message_service = MessageService()