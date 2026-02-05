import logging

from aiogram.types import Message

from bot.config.flags import REMOVE_CHAT_ENABLE
from bot.utils.chat_manager import remove_chat_async
from bot.utils.command_registry import command


@command("remove_chat", flag=REMOVE_CHAT_ENABLE)
async def handle_remove_chat(message: Message) -> None:
    """Обработчик команды /remove_chat."""
    try:
        await message.delete()
    except Exception as e:
        logging.error("Не удалось удалить сообщение пользователя: %s", e)

    chat_id = message.chat.id
    removed_by = message.from_user.username or message.from_user.full_name

    if await remove_chat_async(chat_id, removed_by):
        logging.info("Чат %s успешно помечен как удалённый.", chat_id)
    else:
        logging.debug("Чат %s не найден или уже удалён.", chat_id)
