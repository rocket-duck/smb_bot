import logging
from bot.database import SessionLocal
from bot.models import AdminUser

logger = logging.getLogger(__name__)

def is_user_admin(user_id: int) -> bool:
    """
    Проверяет, является ли пользователь администратором (активен в таблице AdminUser).

    :param user_id: идентификатор пользователя Telegram
    :return: True, если пользователь найден и активен, иначе False
    """
    session = SessionLocal()
    try:
        rec = (
            session.query(AdminUser)
            .filter(
                AdminUser.user_id == str(user_id),
                AdminUser.is_active.is_(True)
            )
            .first()
        )
        return bool(rec)
    except Exception as e:
        logger.error(f"Error checking admin in service: {e}")
        return False
    finally:
        session.close()
