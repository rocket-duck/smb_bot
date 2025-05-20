import logging
import gettext

from aiogram import Router, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

# Internationalization
_ = gettext.gettext

# Bot greeting text
GREETING_TEXT: str = _(
    "Привет! Я бот, который поможет найти ссылки на полезную документацию "
    "или разобраться в процессах тестирования МБ СМБ.\n"
    "Введите /help что бы узнать что я умею"
)

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command(commands=["start"]))
async def handle_start(message: Message) -> None:
    """
    Обрабатывает команду /start.
    Отвечает приветственным сообщением.
    """
    logger.info(
        "Received /start from user %s in chat %s",
        message.from_user.id,
        message.chat.id,
    )
    await message.answer(GREETING_TEXT)

def register(dp: Dispatcher) -> None:
    """
    Регистрирует обработчик /start через Router.
    """
    dp.include_router(router)
