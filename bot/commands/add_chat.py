import logging

from aiogram.types import Message

from bot.config.flags import ADD_CHAT_ENABLE
from bot.utils.chat_manager import add_chat_async
from bot.utils.command_registry import command


@command("add_chat", flag=ADD_CHAT_ENABLE)
async def handle_add_chat(message: Message) -> None:
    try:
        await message.delete()
    except Exception as e:
        logging.error("Не удалось удалить сообщение пользователя: %s", e)

    chat_id = message.chat.id
    chat_title = message.chat.title or "Личный чат"
    added_by = message.from_user.username or message.from_user.full_name

    try:
        await add_chat_async(chat_id, chat_title, added_by)
    except Exception as e:
        logging.error("Ошибка при добавлении чата: %s", e)
