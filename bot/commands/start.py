from aiogram.types import Message

from bot.utils.command_registry import command


@command("start")
async def handle_start(message: Message):
    """Обрабатывает команду /start."""
    await message.answer(
        "Привет! Я бот, который поможет найти ссылки на полезную документацию "
        "или разобраться в процессах тестирования МБ СМБ.\n"
        "Введите /help что бы узнать что я умею"
    )
