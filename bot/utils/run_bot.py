import logging
import asyncio
import pkgutil
import importlib

from aiogram import Bot, Dispatcher
from bot.database import init_db
from bot.config.tokens import API_TOKEN
from bot.services.commands_service import set_bot_commands

import bot.services.menu_service as menu_module
import bot.messages.messages as messages_module
import bot.commands as commands_pkg

async def register_handlers(dp: Dispatcher):
    # Динамическая регистрация обработчиков команд
    for _, module_name, _ in pkgutil.iter_modules(commands_pkg.__path__):
        module = importlib.import_module(f"{commands_pkg.__name__}.{module_name}")
        if hasattr(module, 'register'):
            module.register(dp)

    # Регистрация обработчика меню из bot.services.menu_service
    if hasattr(menu_module, 'register'):
        menu_module.register(dp)

    # Регистрация глобального обработчика сообщений
    if hasattr(messages_module, 'register_message_handlers'):
        messages_module.register_message_handlers(dp)


async def run_bot():
    """
    Главная функция для запуска бота.
    """
    logging.basicConfig(level=logging.INFO)

    # Инициализация базы данных с обработкой ошибок
    try:
        init_db()
    except Exception as e:
        logging.error(f"Database initialization failed: {e}")
        return

    # Инициализация бота и диспетчера с использованием контекстного менеджера
    async with Bot(token=API_TOKEN) as tg_bot:
        dp = Dispatcher()
        try:
           await tg_bot.get_me()
        except Exception as e:
            logging.error(f"Error while getting bot username: {e}")
            return

        await register_handlers(dp)

        # Устанавливаем команды, передавая напрямую экземпляр tg_bot
        await set_bot_commands(tg_bot, user_is_admin=True)

        # Запуск бота с graceful shutdown
        logging.info("Запуск бота...")
        await tg_bot.delete_webhook(drop_pending_updates=True)
        try:
            await dp.start_polling(tg_bot)
        finally:
            logging.info("Bot stopped gracefully.")


if __name__ == '__main__':
    asyncio.run(run_bot())
