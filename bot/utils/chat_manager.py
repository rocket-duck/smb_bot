import logging
from datetime import datetime

from aiogram.types import Message
from sqlalchemy import select

from bot.database import SessionLocal
from bot.models import Chat

logger = logging.getLogger(__name__)


async def add_chat_async(chat_id: int, chat_title: str, added_by: str) -> None:
    """Добавляет чат в базу данных или восстанавливает его, если он был удалён."""
    async with SessionLocal() as session:
        try:
            result = await session.execute(
                select(Chat).filter(Chat.chat_id == str(chat_id))
            )
            existing_chat = result.scalars().first()
            if existing_chat:
                if existing_chat.deleted:
                    existing_chat.deleted = False
                    existing_chat.deleted_by = None
                    existing_chat.deleted_at = None
                    await session.commit()
                    logger.info(f"Чат {chat_id} восстановлен.")
                else:
                    logger.debug(
                        f"Чат {chat_id} уже существует в базе данных."
                    )
                return

            new_chat = Chat(
                chat_id=str(chat_id),
                title=chat_title,
                added_by=added_by,
                added_at=datetime.now(),
                deleted=False,
            )
            session.add(new_chat)
            await session.commit()
            logger.info(
                f"Чат {chat_id} ({chat_title}) добавлен в базу данных пользователем {added_by}."
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"Ошибка при добавлении чата {chat_id}: {e}")
            raise


async def remove_chat_async(chat_id: int, removed_by: str) -> bool:
    """Помечает чат как удалённый."""
    async with SessionLocal() as session:
        try:
            result = await session.execute(
                select(Chat).filter(Chat.chat_id == str(chat_id))
            )
            chat = result.scalars().first()
            if not chat:
                logger.debug(f"Чат {chat_id} не найден в базе данных.")
                return False
            if chat.deleted:
                logger.debug(
                    f"Чат {chat_id} ({chat.title}) уже помечен как удалённый."
                )
                return False

            chat.deleted = True
            chat.deleted_by = removed_by
            chat.deleted_at = datetime.utcnow()
            await session.commit()
            logger.info(
                f"Чат {chat_id} ({chat.title}) помечен как удалённый пользователем {removed_by}."
            )
            return True
        except Exception as e:
            await session.rollback()
            logger.error(f"Ошибка при удалении чата {chat_id}: {e}")
            return False


async def is_user_admin(message: Message) -> bool:
    """Проверяет, является ли пользователь администратором чата."""
    try:
        chat_administrators = await message.bot.get_chat_administrators(
            message.chat.id
        )
        return any(
            admin.user.id == message.from_user.id for admin in chat_administrators
        )
    except Exception as e:
        logger.error(f"Ошибка при проверке администратора: {e}")
        return False


async def get_all_chats_async():
    async with SessionLocal() as session:
        try:
            result = await session.execute(select(Chat))
            chats = result.scalars().all()
            result_list = []
            for chat in chats:
                result_list.append(
                    {
                        "chat_id": chat.chat_id,
                        "title": chat.title,
                        "deleted": chat.deleted,
                    }
                )
            return result_list
        except Exception as e:
            logger.error(f"Ошибка при получении списка чатов: {e}")
            return []
