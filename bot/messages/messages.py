from bot.config.flags import BOT_TAG_ENABLE
from bot.config.tokens import ADMIN_USER_ID
import logging
from collections import deque
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from typing import Dict, Set

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
from bot.services.message_parse_service import parse_message_service
from bot.services.best_qa_participants_service import update_participant

logger = logging.getLogger(__name__)


router = Router()

_HISTORY: Dict[int, deque] = {}
_DISLIKED: Dict[int, Set[str]] = {}

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
    # Build and update context history
    hist = _HISTORY.setdefault(message.chat.id, deque(maxlen=5))
    context = list(hist)
    results = parse_message_service.find_links(keyword, context=context, chat_id=message.chat.id)
    hist.append(keyword)
    # Process and send results
    sent_messages = await message_service.process_results(message, results)
    for sent in sent_messages:
        # Attach inline feedback buttons to each message
        feedback_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="👍", callback_data="feedback:like"),
                    InlineKeyboardButton(text="👎", callback_data="feedback:dislike"),
                ]
            ]
        )
        await sent.edit_reply_markup(reply_markup=feedback_keyboard)
        logger.info("Attached inline feedback buttons to message %s", sent.message_id)

    # === 2. Fan triggers: маслина, картинки, кто и прочее (но только если не был тег бота) ===
    logger.debug("Processing fan triggers.")
    await handle_fan_triggers(message)


def register_message_handlers(dp: Dispatcher) -> None:
    dp.include_router(router)


@router.callback_query(lambda c: c.data == "feedback:dislike")
async def _handle_dislike(query: CallbackQuery):
    logger.info(
        "Feedback dislike received from user %s in chat %s for message %s",
        query.from_user.id,
        query.message.chat.id,
        query.message.message_id
    )
    logger.info("ADMIN_USER_ID=%s (type %s), from_user.id=%s (type %s)",
                ADMIN_USER_ID, type(ADMIN_USER_ID),
                query.from_user.id, type(query.from_user.id))
    user_id = query.from_user.id
    # Compare as strings to avoid type mismatches
    if str(user_id) == str(ADMIN_USER_ID):
        # Admin: delete the bot's message
        await query.bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)
        logger.info("Admin %s deleted message %s", user_id, query.message.message_id)
    else:
        # Other users: hide feedback buttons
        await query.message.edit_reply_markup(reply_markup=None)
        logger.info("User %s hid feedback buttons on message %s", user_id, query.message.message_id)
    # Record dislike for last keyword and specific URL
    chat_id = query.message.chat.id
    hist = _HISTORY.get(chat_id)
    if hist:
        last_kw = hist[-1]
        # Register URL-level dislike under the specific keyword
        msg_text = query.message.text or ""
        url = msg_text.splitlines()[-1] if msg_text else None
        if url:
            parse_message_service.register_dislike(chat_id, last_kw, url)
    await query.answer()

@router.callback_query(lambda c: c.data == "feedback:like")
async def _handle_like(query: CallbackQuery):
    logger.info(
        "Feedback like received from user %s in chat %s for message %s",
        query.from_user.id,
        query.message.chat.id,
        query.message.message_id
    )
    # Hide inline feedback buttons on like
    await query.message.edit_reply_markup(reply_markup=None)
    await query.answer()
