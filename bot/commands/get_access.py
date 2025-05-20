import logging
import asyncio

from datetime import datetime, timezone
from typing import Tuple
from html import escape
from aiogram import Router, types, Dispatcher
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from bot.services.access_service import has_access, grant_access
from bot.config.flags import GET_ACCESS_ENABLE
from bot.config.tokens import ADMIN_USER_ID


logger = logging.getLogger(__name__)
router = Router()


class AccessCallback(CallbackData, prefix="access"):
    action: str
    user_id: str


@router.message.middleware()
async def check_get_access_enabled(handler, event, data):
    """
    Middleware to block /get_access when feature flag is off.
    """
    if not GET_ACCESS_ENABLE:
        logger.debug("GET_ACCESS_ENABLE is False.")
        await event.answer("Команда временно отключена.")
        return
    return await handler(event, data)


import functools
def catch_exceptions(fn):
    """
    Decorator to catch unexpected errors in handlers.
    """
    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Unexpected error in {fn.__name__}: {e}")
            target = args[0]
            # Send generic error reply for both Message and CallbackQuery
            await target.answer("Произошла внутренняя ошибка. Попробуйте позже.")
    return wrapper


def prepare_admin_request(message: types.Message) \
        -> Tuple[str, types.InlineKeyboardMarkup]:
    user_id = message.from_user.id
    raw_full_name = message.from_user.full_name or ""
    raw_username = message.from_user.username or ""
    full_name = escape(raw_full_name)
    username = escape(raw_username)
    request_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    admin_text = (
        f"Запрос на доступ!\n\n"
        f"User ID: {user_id}\n"
        f"Full Name: {full_name}\n"
        f"Username: @{username}\n"
        f"Время запроса: {request_time}"
    )
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Принять",
                                    callback_data=f"access:accept:{user_id}")],
        [types.InlineKeyboardButton(text="Отклонить",
                                    callback_data=f"access:decline:{user_id}")]
    ])
    return admin_text, keyboard


@router.message(
    Command(commands=["get_access"]),
    lambda message: message.chat.type == "private"
)
@catch_exceptions
async def handle_get_access(message: types.Message) -> None:
    """
    Handler for /get_access: initiates access request.
    """
    logger.info(f"handle_get_access called by user {message.from_user.id}")
    loop = asyncio.get_running_loop()
    # Check existing access
    if await loop.run_in_executor(None, has_access, message.from_user.id):
        await message.answer("Доступ уже предоставлен")
        return

    # No access yet, request sent to admin
    await message.answer("Ожидайте предоставление доступа.")
    admin_text, keyboard = prepare_admin_request(message)
    try:
        await message.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=admin_text,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error("Ошибка отправки запроса администратору: %s", e)
        await message.answer(
            "Произошла ошибка при отправке запроса администратору. Попробуйте позже."
        )


@router.callback_query(AccessCallback.filter())
@catch_exceptions
async def handle_accept_callback(
    callback: types.CallbackQuery,
    callback_data: AccessCallback
) -> None:
    """
    Grant access to the user based on admin approval.
    """
    logger.info(f"handle_accept_callback by admin {callback.from_user.id} for user {callback_data.user_id}")
    loop = asyncio.get_running_loop()
    target_user_id = int(callback_data.user_id)
    admin_info = {
        "user_id": callback.from_user.id,
        "full_name": callback.from_user.full_name or "",
        "username": callback.from_user.username or ""
    }
    # Grant access via service
    await loop.run_in_executor(None, grant_access, admin_info, target_user_id)
    callback.message.edit_reply_markup(reply_markup=None)
    callback.bot.send_message(
        chat_id=target_user_id,
        text="Доступ предоставлен"
    )
    await callback.answer("Доступ предоставлен.")


@router.callback_query(AccessCallback.filter())
@catch_exceptions
async def handle_decline_callback(
    callback: types.CallbackQuery,
    callback_data: AccessCallback
) -> None:
    target_user_id = int(callback_data.user_id)
    """
    Decline access request.
    """
    logger.info(f"handle_decline_callback by admin {callback.from_user.id} for user {target_user_id}")
    try:
        callback.message.edit_reply_markup(reply_markup=None)
        callback.bot.send_message(chat_id=target_user_id,
                                  text="Вам отказано в доступе")
        await callback.answer("Доступ отклонён.")
    except Exception as e:
        logger.error("Ошибка обработки decline callback: %s", e)
        await callback.answer("Произошла ошибка. Попробуйте позже.")


def register(dp: Dispatcher) -> None:
    """
    Регистрирует обработчики get_access и процессинг callback’ов через Router.
    """
    dp.include_router(router)
