import logging
from aiogram.filters import Command
from aiogram.types import Message
from bot.config.flags import ADD_CHAT_ENABLE
from bot.utils.chat_manager import add_chat, is_user_admin

logging.basicConfig(level=logging.DEBUG)


async def can_add_chat(message: Message) -> bool:
    if not ADD_CHAT_ENABLE:
        logging.debug("Команда /add_chat временно отключена.")
        return False

    if not await is_user_admin(message):
        logging.debug("Команда /add_chat доступна только администраторам чата.")
        return False

    return True


async def handle_add_chat(message: Message) -> None:
    try:
        await message.delete()
    except Exception as e:
        logging.error(f"Не удалось удалить сообщение пользователя: {e}")

    if not await can_add_chat(message):
        return

    chat_id = message.chat.id
    chat_title = message.chat.title or "Личный чат"
    added_by = message.from_user.username or message.from_user.full_name

    try:
        add_chat(chat_id, chat_title, added_by)
    except Exception as e:
        logging.error(f"Ошибка при добавлении чата: {e}")


def register_add_chat_handler(dp) -> None:
    dp.message.register(handle_add_chat,
                        Command(commands=["add_chat"]))
