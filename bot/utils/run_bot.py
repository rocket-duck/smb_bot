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
    asyncio.create_task(schedule_good_morning(bot))

    # Запуск бота
    logging.info("Запуск бота...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run_bot())
