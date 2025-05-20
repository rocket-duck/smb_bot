from aiogram import Router, types, Dispatcher
from aiogram.filters import Command
from bot.config.flags import GET_EPA_GUIDE_ENABLE

import logging
import functools

logger = logging.getLogger(__name__)

router = Router()

@router.message.middleware()
async def check_guide_enabled(handler, event, data):
    """
    Middleware: блокирует обработчик, если GET_EPA_GUIDE_ENABLE = False.
    """
    if not GET_EPA_GUIDE_ENABLE:
        logger.debug("GET_EPA_GUIDE_ENABLE is False.")
        await event.answer("Команда временно отключена.")
        return
    return await handler(event, data)

def catch_exceptions(fn):
    """
    Декоратор для перехвата непредвиденных ошибок в хендлере.
    """
    @functools.wraps(fn)
    async def wrapper(message: types.Message) -> None:
        try:
            await fn(message)
        except Exception as e:
            logger.exception(f"epa_guide error: {e}")
            await message.reply("Произошла внутренняя ошибка. Попробуйте позже.")
    return wrapper

@router.message(Command("epa_guide", prefix="/"))
@catch_exceptions
async def handle_epa_guide(message: types.Message) -> None:
    """
    Отдаёт ссылки на гайды по ЕПА.
    :param message: входящее сообщение Telegram
    """
    logger.info(f"handle_epa_guide called by user {message.from_user.id} in chat {message.chat.id}")

    text = (
        "Авторизация по старой цепочке (ЕПА-3): https://sfera.inno.local/knowledge/pages?id=1513112\n"
        "Авторизация по новой цепочке (ЕПА-10): https://sfera.inno.local/knowledge/pages?id=1513113"
    )
    await message.answer(text)


# Регистрация обработчиков через Router
def register(dp: Dispatcher) -> None:
    """
    Регистрирует обработчики /epa_guide через Router.
    """
    dp.include_router(router)
