from bot.config.flags import BOT_TAG_ENABLE
import logging

from aiogram import Router, Dispatcher
from aiogram.types import Message

from bot.messages.filters import (
    sanitize_text,
    should_process_text,
    no_fsm_filter,
    skip_empty,
    skip_slash_command,
)
from bot.messages.triggers import handle_fan_triggers, handle_bot_tag
from bot.services.message_service import message_service
from bot.services.parse_message_service import parse_message_service
from bot.services.best_qa_participants_service import update_participant

logger = logging.getLogger(__name__)


router = Router()

@router.message.middleware()  # Centralized error handling for all message handlers
async def error_middleware(handler, event: Message, data: dict):
    try:
        return await handler(event, data)
    except Exception as e:
        logger.exception("Unexpected error in handler: %s", e)
        # Notify the user of a generic internal error
        await event.answer("Извините, произошла внутренняя ошибка. Попробуйте позже.")
        return None


@router.message(skip_slash_command, skip_empty, no_fsm_filter)
async def handle_message(message: Message) -> None:
    logger.info(
        "Received message from user %s in chat %s: %s",
        message.from_user.id,
        message.chat.id,
        message.text
    )

    # === 1. Реакция на тег бота (например, отправка видео) — теперь самым первым делом ===
    logger.debug("Checking for bot tag...")
    handled = await handle_bot_tag(message, BOT_TAG_ENABLE)
    if handled:
        logger.debug("Bot tag detected and handled, skipping further processing.")
        return

    text = sanitize_text(message.text.strip())
    update_participant(message)

    if not should_process_text(text):
        return

    keyword = text.lower()
    results = parse_message_service.find_links(keyword)
    await message_service.process_results(message, results)

    # === 2. Fan triggers: маслина, картинки, кто и прочее (но только если не был тег бота) ===
    logger.debug("Processing fan triggers.")
    await handle_fan_triggers(message)


def register_message_handlers(dp: Dispatcher) -> None:
    dp.include_router(router)
