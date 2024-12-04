import asyncio
import logging
from aiogram import Bot, Dispatcher
from config.token import API_TOKEN
from commands.start import register_start_handler
from commands.help import register_help_handler
from commands.docs import register_docs_handler
from modules.buttons import register_button_handlers
from modules.messages import register_message_handlers

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def register_handlers():
    """
    Регистрирует все обработчики бота.
    """
    register_start_handler(dp)
    register_help_handler(dp)
    register_docs_handler(dp)
    register_button_handlers(dp)
    register_message_handlers(dp)

async def main():
    logging.info("Запуск бота...")
    register_handlers()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())