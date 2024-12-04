from aiogram.filters import Command
from aiogram.types import Message

async def handle_help(message: Message):
    """
    Обрабатывает команду /help.

    :param message: Сообщение от пользователя
    """
    help_text = (
        "Я бот для работы с доступами и документацией. Вот что я умею:\n"
        "- /start — запустить бота и открыть главное меню.\n"
        "- /docs — показать документацию.\n"
        "- /help — показать это сообщение.\n"
        "Вы можете писать ключевые слова, чтобы получить ссылки на документацию."
    )
    await message.answer(help_text)

def register_help_handler(dp):
    """
    Регистрирует обработчик команды /help.

    :param dp: Экземпляр Dispatcher
    """
    dp.message.register(handle_help, Command(commands=["help"]))
