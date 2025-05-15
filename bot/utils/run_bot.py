import logging
import asyncio
from aiogram import Bot, Dispatcher
from bot.config.tokens import API_TOKEN
from bot.database import init_db
from bot.utils.handlers import register_handlers
from bot.modules.commands_list import set_bot_commands


async def run_bot():
    """
    Главная функция для запуска бота.
    """
    logging.basicConfig(level=logging.DEBUG)

    # Инициализация базы данных
    init_db()

    # Инициализация бота и диспетчера
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()

    # Регистрация обработчиков
    register_handlers(dp)

    # Устанавливаем команды, передавая напрямую экземпляр bot
    await set_bot_commands(bot, user_is_admin=True)

    # Запуск бота
    logging.info("Запуск бота...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(run_bot())
