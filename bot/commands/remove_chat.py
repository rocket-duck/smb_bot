import logging
from aiogram.filters import Command
from aiogram.types import Message
from bot.config.flags import REMOVE_CHAT_ENABLE
from bot.utils.chat_manager import remove_chat, is_user_admin

logging.basicConfig(level=logging.DEBUG)


async def handle_remove_chat(message: Message) -> None:
    """
    Обработчик команды /remove_chat.
    Если команда включена и вызывающий является администратором,
    чат помечается как удалённый в базе данных.
    После чего сообщение пользователя удаляется.
    """
    try:
        await message.delete()
    except Exception as e:
        logging.error(f"Не удалось удалить сообщение пользователя: {e}")

    if not REMOVE_CHAT_ENABLE:
        logging.debug("Команда /remove_chat временно отключена.")
        return

    if not await is_user_admin(message):
        logging.debug("Команда /remove_chat доступна только "
                      "администраторам чата.")
        return

    chat_id = message.chat.id
    removed_by = message.from_user.username or message.from_user.full_name

    if remove_chat(chat_id, removed_by):
        logging.info(f"Чат {chat_id} успешно помечен как удалённый.")
    else:
        logging.debug(f"Чат {chat_id} не найден или уже удалён.")


def register_remove_chat_handler(dp) -> None:
    dp.message.register(handle_remove_chat, Command(commands=["remove_chat"]))
