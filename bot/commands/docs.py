from aiogram.filters import Command
from aiogram.types import Message
from bot.menu.main_menu import create_main_menu

async def handle_docs(message: Message):
    """
    Обрабатывает команду /docs.

    :param message: Сообщение от пользователя
    """
    await message.answer(
        "Вот доступные разделы документации. Выберите из меню ниже:",
        reply_markup=create_main_menu(),
    )

def register_docs_handler(dp):
    """
    Регистрирует обработчик команды /docs.

    :param dp: Экземпляр Dispatcher
    """
    dp.message.register(handle_docs, Command(commands=["docs"]))
