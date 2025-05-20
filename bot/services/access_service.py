import logging
from datetime import datetime
from html import escape
from bot.database import SessionLocal
from bot.models import AdminUser

logger = logging.getLogger(__name__)

def has_access(user_id: int) -> bool:
    """
    Проверяет, есть ли активный доступ у пользователя.
    """
    session = SessionLocal()
    try:
        record = session.query(AdminUser).filter(
            AdminUser.user_id == str(user_id),
            AdminUser.is_active.is_(True)
        ).first()
        return record is not None
    except Exception as e:
        logger.error("Ошибка проверки доступа: %s", e)
        return False
    finally:
        session.close()

def grant_access(admin_user: dict, target_user_id: int) -> None:
    """
    Добавляет или активирует запись доступа для target_user_id.
    admin_user: dict с ключами 'user_id', 'full_name', 'username'.
    """
    session = SessionLocal()
    try:
        user_id_str = str(admin_user["user_id"])
        record = session.query(AdminUser).filter(
            AdminUser.user_id == user_id_str
        ).first()
        if not record:
            record = AdminUser(
                user_id=user_id_str,
                full_name=escape(admin_user.get("full_name", "")),
                username=escape(admin_user.get("username", "")),
                added_at=datetime.utcnow(),
                is_active=True
            )
            session.add(record)
        else:
            if not record.is_active:
                record.is_active = True
                record.added_at = datetime.utcnow()
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error("Ошибка grant_access: %s", e)
        raise
    finally:
        session.close()