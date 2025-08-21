import logging
from aiogram import Router, types

from bot.config.flags import GET_CHAT_LIST
from bot.utils.chat_manager import get_all_chats_async
from bot.utils.command_registry import command

logger = logging.getLogger(__name__)
router = Router()


@command("chat_list", flag=GET_CHAT_LIST, admin_only=True, router=router)
async def handle_chat_list(message: types.Message) -> None:
    chats = await get_all_chats_async()
    if not chats:
        await message.answer("Список чатов пуст.")
        return

    response_lines = ["Список известных чатов:"]
    for chat in chats:
        status = "активен" if not chat.get("deleted", False) else "удалён"
        title = chat.get("title") or "Без названия"
        response_lines.append(f"{title} (ID: {chat.get('chat_id')}) - {status}")
    response_text = "\n".join(response_lines)
    await message.answer(response_text)
