from aiogram.filters import Command
from aiogram.types import Message
from bot.menu.main_menu import create_main_menu

async def handle_start(message: Message):
    """
    Обрабатывает команду /start.

    :param message: Сообщение от пользователя
    """
    await message.answer(
        "Привет! Я бот, который помогает с доступами и документацией.\nВыберите нужное из меню ниже:",
        reply_markup=create_main_menu(),
    )

def register_start_handler(dp):
    """
    Регистрирует обработчик команды /start.

    :param dp: Экземпляр Dispatcher
    """
    dp.message.register(handle_start, Command(commands=["start"]))
