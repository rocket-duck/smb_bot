import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any

logger = logging.getLogger(__name__)

class RecentLinksService:
    """
    Service for tracking recently sent links per chat and filtering them out based on TTL.
    """
    def __init__(self, ttl_minutes: int):
        self.ttl_minutes = ttl_minutes
        # Structure: {chat_id: {url: datetime_last_sent}}
        self.cache: Dict[int, Dict[str, datetime]] = {}

    def filter(self, chat_id: int, results: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """
        Filters out links that have been sent within the TTL for the given chat.
        :param chat_id: Telegram chat identifier.
        :param results: List of tuples (name, url) to filter.
        :return: Filtered list of (name, url) not sent within TTL.
        """
        now = datetime.now()
        chat_cache = self.cache.setdefault(chat_id, {})
        filtered: List[Tuple[str, str]] = []
        for name, url in results:
            last_time = chat_cache.get(url)
            if last_time and (now - last_time) < timedelta(minutes=self.ttl_minutes):
                logger.debug(f"Skipping recently sent link '{url}' for chat {chat_id}.")
            else:
                filtered.append((name, url))
                chat_cache[url] = now
        return filtered
