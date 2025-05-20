import logging

from typing import List, Dict
from bot.database import SessionLocal
from bot.models import Chat

logger = logging.getLogger(__name__)

def add_chat(chat_id: int, title: str, added_by: str) -> None:
    """
    Добавляет новый чат или реанимирует ранее удалённый.
    :param chat_id: идентификатор чата
    :param title: название чата
    :param added_by: кто добавил чат (username или full_name)
    """
    session = SessionLocal()
    try:
        # Ищем существующую запись
        record = session.query(Chat).filter(Chat.chat_id == str(chat_id)).first()
        if record is None:
            record = Chat(
                chat_id=str(chat_id),
                title=title,
                added_by=added_by,
                is_deleted=False
            )
            session.add(record)
            logger.info(f"Added new chat {chat_id} by {added_by}")
        else:
            # Обновляем название и снимаем метку удаления
            record.title = title
            record.is_deleted = False
            logger.info(f"Reactivated chat {chat_id} by {added_by}")
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error in add_chat for {chat_id}: {e}")
        raise
    finally:
        session.close()

def remove_chat(chat_id: int, removed_by: str) -> None:
    """
    Отмечает чат как удалённый.
    :param chat_id: идентификатор чата
    :param removed_by: кто выполнил удаление
    """
    session = SessionLocal()
    try:
        record = session.query(Chat).filter(
            Chat.chat_id == str(chat_id),
            Chat.is_deleted.is_(False)
        ).first()
        if record:
            record.is_deleted = True
            record.removed_by = removed_by
            session.commit()
            logger.info(f"Removed chat {chat_id} by {removed_by}")
    except Exception as e:
        session.rollback()
        logger.error(f"Error in remove_chat for {chat_id}: {e}")
        raise
    finally:
        session.close()

def get_all_chats() -> List[Dict[str, object]]:
    """
    Возвращает список всех чатов с их состоянием.
    :return: список словарей с ключами: chat_id, title, deleted
    """
    session = SessionLocal()
    try:
        records = session.query(Chat).all()
        return [
            {
                "chat_id": int(r.chat_id),
                "title": r.title,
                "deleted": bool(r.is_deleted)
            }
            for r in records
        ]
    except Exception as e:
        logger.error(f"Error in get_all_chats: {e}")
        return []
    finally:
        session.close()
