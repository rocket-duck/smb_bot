from aiogram import Router, types, Dispatcher
from aiogram.filters import Command
from bot.config.flags import GET_EPA_CONTACTS_ENABLE
import logging
import functools

logger = logging.getLogger(__name__)

def catch_exceptions(fn):
    """
    Decorator to catch unexpected errors in handler.
    """
    @functools.wraps(fn)
    async def wrapper(message: types.Message) -> None:
        try:
            await fn(message)
        except Exception as e:
            logger.exception(f"Error in epa_contacts handler: {e}")
            await message.reply("Произошла внутренняя ошибка. Попробуйте позже.")
    return wrapper

router = Router()

@router.message.middleware()
async def check_enabled(handler, event, data):
    """
    Middleware: blocks handler if feature flag is False.
    """
    if not GET_EPA_CONTACTS_ENABLE:
        logger.debug("GET_EPA_CONTACTS_ENABLE is False.")
        await event.answer("Команда временно отключена.")
        return
    return await handler(event, data)

@router.message(Command("epa_contacts", prefix="/"))
@catch_exceptions
async def handle_epa_contacts(message: types.Message) -> None:
    logger.info(f"handle_epa_contacts called by user {message.from_user.id}")

    text = (
        "Контакты ЕПА для связи: https://sfera.inno.local/knowledge/pages?id=1524162"
    )
    await message.answer(text)

def register(dp: Dispatcher) -> None:
    """
    Регистрирует обработчик /epa_contacts через Router.
    """
    dp.include_router(router)
