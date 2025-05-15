from aiogram.filters import Command
from aiogram.types import Message


async def handle_start(message: Message):
    """
    Обрабатывает команду /start.
    :param message: Сообщение от пользователя
    """
    await message.answer(
        "Привет! Я бот, который поможет найти ссылки на полезную документацию "
        "или разобраться в процессах тестирования МБ СМБ.\n"
        "Введите /help что бы узнать что я умею"
    )


def register_start_handler(dp):
    """
    Регистрирует обработчики команды /start и кнопки "Список команд".
    :param dp: Экземпляр Dispatcher
    """
    dp.message.register(handle_start, Command(commands=["start"]))
