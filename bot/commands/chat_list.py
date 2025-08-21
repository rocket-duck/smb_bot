import logging
from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy import select

from bot.utils.chat_manager import get_all_chats_async
from bot.database import SessionLocal
from bot.models import AdminUser

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("chat_list", prefix="/"))
async def handle_chat_list(message: types.Message) -> None:
    # Проверяем, есть ли активная запись для пользователя в таблице admin_users
    async with SessionLocal() as session:
        try:
            result = await session.execute(
                select(AdminUser).filter(
                    AdminUser.user_id == str(message.from_user.id),
                    AdminUser.is_active.is_(True),
                )
            )
            admin_record = result.scalars().first()
        except Exception as e:
            logger.error("Ошибка проверки прав администратора: %s", e)
            admin_record = None

    if not admin_record:
        await message.answer("У вас нет прав для использования этой команды.\n"
                             "Запросить права вы можете командой /get_access")
        return

    # Получаем список чатов
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


def register_chat_list_handler(dp) -> None:
    dp.message.register(handle_chat_list, Command(commands=["chat_list"]))
