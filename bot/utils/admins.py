import logging
from sqlalchemy import select

from bot.database import SessionLocal
from bot.models import AdminUser

logger = logging.getLogger(__name__)


async def is_user_admin_db(user_id: int) -> bool:
    """Проверяет, имеет ли пользователь права администратора."""
    async with SessionLocal() as session:
        try:
            result = await session.execute(
                select(AdminUser).filter(
                    AdminUser.user_id == str(user_id),
                    AdminUser.is_active.is_(True),
                )
            )
            return result.scalars().first() is not None
        except Exception as e:
            logger.error("Ошибка проверки прав администратора: %s", e)
            return False
