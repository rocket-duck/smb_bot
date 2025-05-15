import logging
from datetime import datetime

from aiogram.types import Message
from bot.database import SessionLocal
from bot.models import Chat

logger = logging.getLogger(__name__)


def add_chat(chat_id: int, chat_title: str, added_by: str) -> None:
    """
    Добавляет чат в базу данных или восстанавливает его,
    если он ранее был помечен как удалённый.

    :param chat_id: Идентификатор чата.
    :param chat_title: Название чата.
    :param added_by: Имя или username пользователя, добавившего чат.
    """
    session = SessionLocal()
    try:
        # Приводим chat_id к строке для единообразия хранения
        existing_chat = (session.query(Chat)
                         .filter(Chat.chat_id == str(chat_id)).first())
        if existing_chat:
            if existing_chat.deleted:
                existing_chat.deleted = False
                existing_chat.deleted_by = None
                existing_chat.deleted_at = None
                session.commit()
                logger.info(f"Чат {chat_id} восстановлен.")
            else:
                logger.debug(f"Чат {chat_id} уже существует в базе данных.")
            return

        new_chat = Chat(
            chat_id=str(chat_id),
            title=chat_title,
            added_by=added_by,
            added_at=datetime.now(),
            deleted=False
        )
        session.add(new_chat)
        session.commit()
        logger.info(f"Чат {chat_id} ({chat_title}) добавлен в "
                    f"базу данных пользователем {added_by}.")
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при добавлении чата {chat_id}: {e}")
        raise
    finally:
        session.close()


def remove_chat(chat_id: int, removed_by: str) -> bool:
    """
    Помечает чат как удалённый в базе данных.

    :param chat_id: Идентификатор чата.
    :param removed_by: Имя или username пользователя, инициировавшего удаление.
    :return: True, если чат найден и успешно помечен, иначе False.
    """
    session = SessionLocal()
    try:
        chat = session.query(Chat).filter(Chat.chat_id == str(chat_id)).first()
        if not chat:
            logger.debug(f"Чат {chat_id} не найден в базе данных.")
            return False
        if chat.deleted:
            logger.debug(f"Чат {chat_id} ({chat.title}) уже "
                         f"помечен как удалённый.")
            return False

        chat.deleted = True
        chat.deleted_by = removed_by
        chat.deleted_at = datetime.utcnow()
        session.commit()
        logger.info(f"Чат {chat_id} ({chat.title}) помечен "
                    f"как удалённый пользователем {removed_by}.")
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при удалении чата {chat_id}: {e}")
        return False
    finally:
        session.close()


async def is_user_admin(message: Message) -> bool:
    """
    Проверяет, является ли пользователь администратором чата.

    :param message: Объект сообщения.
    :return: True, если пользователь является администратором, иначе False.
    """
    try:
        chat_administrators = await message.bot.get_chat_administrators(
            message.chat.id)
        return any(admin.user.id == message.from_user.id
                   for admin in chat_administrators)
    except Exception as e:
        logger.error(f"Ошибка при проверке администратора: {e}")
        return False


def get_all_chats():
    session = SessionLocal()
    try:
        chats = session.query(Chat).all()
        result = []
        for chat in chats:
            result.append({
                "chat_id": chat.chat_id,
                "title": chat.title,
                "deleted": chat.deleted
            })
        return result
    except Exception as e:
        logger.error(f"Ошибка при получении списка чатов: {e}")
        return []
    finally:
        session.close()
