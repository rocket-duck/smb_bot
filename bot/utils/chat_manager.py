import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from bot.database import SessionLocal
from bot.models import Chat

logger = logging.getLogger(__name__)


async def add_chat_async(chat_id: int, chat_title: str, added_by: str) -> None:
    """Добавляет чат в базу данных или восстанавливает его, если он был удалён."""
    async with SessionLocal() as session:
        try:
            result = await session.execute(
                select(Chat).filter(Chat.chat_id == chat_id)
            )
            existing_chat = result.scalars().first()
            if existing_chat:
                if existing_chat.deleted:
                    existing_chat.deleted = False
                    existing_chat.deleted_by = None
                    existing_chat.deleted_at = None
                    await session.commit()
                    logger.info("Чат %s восстановлен.", chat_id)
                else:
                    logger.debug("Чат %s уже существует в базе данных.", chat_id)
                return

            new_chat = Chat(
                chat_id=chat_id,
                title=chat_title,
                added_by=added_by,
                added_at=datetime.now(UTC),
                deleted=False,
            )
            session.add(new_chat)
            await session.commit()
            logger.info(
                "Чат %s (%s) добавлен в базу данных пользователем %s.",
                chat_id,
                chat_title,
                added_by,
            )
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Ошибка при добавлении чата %s: %s", chat_id, e)
            raise


async def remove_chat_async(chat_id: int, removed_by: str) -> bool:
    """Помечает чат как удалённый."""
    async with SessionLocal() as session:
        try:
            result = await session.execute(
                select(Chat).filter(Chat.chat_id == chat_id)
            )
            chat = result.scalars().first()
            if not chat:
                logger.debug("Чат %s не найден в базе данных.", chat_id)
                return False
            if chat.deleted:
                logger.debug("Чат %s (%s) уже помечен как удалённый.", chat_id, chat.title)
                return False

            chat.deleted = True
            chat.deleted_by = removed_by
            chat.deleted_at = datetime.now(UTC)
            await session.commit()
            logger.info(
                "Чат %s (%s) помечен как удалённый пользователем %s.",
                chat_id,
                chat.title,
                removed_by,
            )
            return True
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Ошибка при удалении чата %s: %s", chat_id, e)
            return False


async def get_all_chats_async():
    async with SessionLocal() as session:
        try:
            result = await session.execute(select(Chat))
            chats = result.scalars().all()
            return [
                {"chat_id": chat.chat_id, "title": chat.title, "deleted": chat.deleted}
                for chat in chats
            ]
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении списка чатов: %s", e)
            return []
