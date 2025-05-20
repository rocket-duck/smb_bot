import logging
from typing import List, Dict, Any
import asyncio
from aiogram import Router
from aiogram.filters import Command
from aiogram import Dispatcher
from bot.services.chat_service import get_all_chats
from bot.services.admin_service import is_user_admin
from aiogram.types import Message


logger = logging.getLogger(__name__)
router = Router()


# Middleware: проверка прав администратора
@router.message.middleware()
async def admin_only_middleware(handler, event, data):
    """
    Проверяет права администратора перед вызовом любого сообщения /chat_list.
    """
    # Проверка прав админа в executor
    loop = asyncio.get_running_loop()
    try:
        is_admin = await loop.run_in_executor(None, is_user_admin, event.from_user.id)
    except Exception as e:
        logger.error(f"Error checking admin rights: {e}")
        await event.answer("Произошла ошибка при проверке прав.")
        return
    if not is_admin:
        await event.answer(
            "У вас нет прав для использования этой команды.\n"
            "Запросить права вы можете командой /get_access"
        )
        return
    return await handler(event, data)


# Форматирование списка чатов
def format_chat_list(chats: List[Dict[str, Any]]) -> str:
    """
    Форматирует список словарей chat в многострочное сообщение.
    Ограничивает вывод первыми 10 элементами.
    """
    lines = ["Список известных чатов:"]
    for chat in chats:
        status = "активен" if not chat.get("deleted", False) else "удалён"
        title = chat.get("title") or "Без названия"
        lines.append(f"{title} (ID: {chat.get('chat_id')}) - {status}")
    return "\n".join(lines)


async def handle_chat_list(message: Message) -> None:
    """
    Обрабатывает команду /chat_list: получает чаты и отправляет форматированный список.
    """
    logger.info(f"User {message.from_user.id} requested /chat_list in chat {message.chat.id}")
    try:
        # Получение списка чатов в executor, чтобы не блокировать loop
        loop = asyncio.get_running_loop()
        chats = await loop.run_in_executor(None, get_all_chats)
        if not chats:
            await message.answer("Список чатов пуст.")
            return

        text = format_chat_list(chats)
        await message.answer(text)
    except Exception as e:
        logger.exception(f"Unexpected error in handle_chat_list: {e}")
        await message.answer("Произошла внутренняя ошибка.")


router.message.register(handle_chat_list, Command(commands=["chat_list"]))


def register(dp: Dispatcher) -> None:
    """Регистрирует обработчик /chat_list через Router."""
    dp.include_router(router)
