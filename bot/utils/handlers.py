import logging
from aiogram import types


logger = logging.getLogger(__name__)


def register_handlers(dp):
    dp.register_errors_handler(global_error_handler)


async def global_error_handler(update: types.Update,
                               exception: Exception) -> bool:
    """
    Глобальный обработчик ошибок: логирует исключения и уведомляет пользователя.
    """
    logger.exception(f"Exception on update {update}: {exception}")
    # Пытаемся уведомить пользователя о проблеме
    try:
        if update.message:
            await update.message.reply("Извините, что-то пошло не так. "
                                       "Попробуйте позже.")
    except Exception:
        pass
    # Возвращаем True, чтобы Aiogram не продолжал обработку этого исключения
    return True
