import logging
import asyncio
from typing import Callable, Awaitable
from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from aiogram import Router
from bot.config.flags import ADD_CHAT_ENABLE
from bot.services.chat_service import add_chat
from bot.services.admin_service import is_user_admin

logger = logging.getLogger(__name__)



def admin_only(func: Callable[[Message], Awaitable[None]]) -> Callable[[Message], Awaitable[None]]:
    """
    Декоратор: проверяет права администратора перед вызовом команды.
    """
    async def wrapper(message: Message) -> None:
        # Always delete the invocation message
        try:
            await message.delete()
        except Exception as e:
            logger.error(f"Не удалось удалить сообщение пользователя: {e}")

        if not ADD_CHAT_ENABLE:
            logger.debug("Команда /add_chat временно отключена.")
            return
        loop = asyncio.get_running_loop()
        try:
            is_admin = await loop.run_in_executor(None, is_user_admin, message.from_user.id)
        except Exception as e:
            logger.exception(f"Ошибка проверки прав администратора: {e}")
            return
        if not is_admin:
            logger.debug("Команда /add_chat доступна только администраторам.")
            return

        # Allow only group chats
        if message.chat.type != "group":
            logger.debug("Команда /add_chat доступна только в групповых чатах.")
            return

        await func(message)
    return wrapper


@admin_only
async def handle_add_chat(message: Message) -> None:
    """
    Обрабатывает /add_chat: удаляет сообщение и добавляет текущий чат.
    Не оставляет следов вызова.
    """

    # добавление чата
    chat_id = message.chat.id
    chat_title = message.chat.title or "Личный чат"
    added_by = message.from_user.username or message.from_user.full_name

    try:
        add_chat(chat_id, chat_title, added_by)
    except Exception as e:
        logger.exception(f"Ошибка при добавлении чата: {e}")


# Router setup for /add_chat command
router = Router()
router.message.register(handle_add_chat, Command(commands=["add_chat"]))


def register(dp: Dispatcher) -> None:
    """
    Регистрирует роутер для команды /add_chat.
    """
    dp.include_router(router)
