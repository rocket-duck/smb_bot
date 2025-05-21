import logging
import random
import re

from aiogram import Router
from aiogram.types import Message

from bot.config.flags import BOT_TAG_ENABLE, WHO_REQUEST_ENABLE, MASLINA_ENABLE, FAN_TRIGGER_PROBABILITY
from bot.messages.bot_tag import handle_bot_tag
from bot.config.tokens import BOT_USERNAME
from bot.messages.who_request import handle_who_request
from bot.messages.maslina import handle_maslina

router = Router()
logger = logging.getLogger(__name__)

async def handle_fan_triggers(message: Message) -> bool:
    logger.debug(f"handle_fan_triggers called with message text: {message.text!r}")

    if BOT_USERNAME is None:
        logger.warning("BOT_USERNAME is not set, skipping fan triggers.")
        return False

    bot_username_clean = BOT_USERNAME.lstrip('@').lower()
    bot_username_mention = f"@{bot_username_clean}"

    text_lower = (message.text or "").lower()

    pattern = re.compile(rf'(^|\s){re.escape(bot_username_mention)}(\s|$)')

    if pattern.search(text_lower):
        logger.debug("Bot tag detected, calling handle_bot_tag...")
        handled = await handle_bot_tag(message, bot_tag_enable=BOT_TAG_ENABLE)
        if handled:
            logger.debug("handle_bot_tag handled the message, stopping further triggers.")
            return True
        logger.debug("handle_bot_tag did not handle the message, skipping other triggers to avoid duplicates.")
        return True  # Always stop here to avoid running other triggers

    if await handle_maslina(message, maslina_enable=MASLINA_ENABLE):
        return True

    if random.random() < FAN_TRIGGER_PROBABILITY:
        if await handle_who_request(message, who_request_enable=WHO_REQUEST_ENABLE):
            return True

    return False