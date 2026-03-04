import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.config.logging import setup_logging
from bot.config.settings import get_settings
from bot.config.telemetry import setup_sentry
from bot.database import init_db
from bot.modules.commands_list import set_bot_commands
from bot.utils.good_morning import schedule_good_morning
from bot.utils.handlers import register_handlers

_BG_TASKS: set[asyncio.Task] = set()


async def run_bot():
    """
    Главная функция для запуска бота.
    """
    settings = get_settings()
    setup_logging(level=settings.log_level)
    setup_sentry(settings)

    # Инициализация базы данных
    await init_db()

    # Инициализация бота и диспетчера
    bot = Bot(token=settings.api_token)
    dp = Dispatcher()

    # Регистрация обработчиков
    register_handlers(dp)

    # Устанавливаем команды, передавая напрямую экземпляр bot
    await set_bot_commands(bot)

    # Планируем отправку утреннего сообщения (проверка флага внутри модуля)
    morning_task = asyncio.create_task(schedule_good_morning(bot))
    _BG_TASKS.add(morning_task)
    morning_task.add_done_callback(_BG_TASKS.discard)
    morning_task.add_done_callback(
        lambda t: logging.error("schedule_good_morning завершился с ошибкой: %s", t.exception())
        if not t.cancelled() and t.exception()
        else None
    )

    # Запуск бота
    logging.info("Запуск бота...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run_bot())
