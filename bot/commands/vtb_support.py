import logging
import gettext

from aiogram import Router, types, Dispatcher
from aiogram.filters import Command
from bot.config.flags import VTB_SUPPORT_ENABLE

_ = gettext.gettext

# Internationalized support phone text
PHONE_SUPPORT_TEXT: str = _("Телефон поддержки ВТБ — +7 495 981-80-81")

logger = logging.getLogger(__name__)
router = Router()

@router.message.middleware()
async def feature_flag_middleware(handler, event, data):
    """
    Middleware to check VTB_SUPPORT_ENABLE flag.
    """
    if not VTB_SUPPORT_ENABLE:
        await event.answer(_("Команда временно отключена."))
        return
    return await handler(event, data)

async def handle_vtb_support(message: types.Message) -> None:
    """
    Обработчик команды /vtb_support: отвечает телефоном поддержки.
    :param message: входящее Telegram-сообщение
    :return: None
    """
    logger.info(
        "vtb_support called by user %s in chat %s",
        message.from_user.id,
        message.chat.id
    )
    await message.answer(PHONE_SUPPORT_TEXT)

from aiogram.filters import Command

# Explicitly register handler on router
router.message.register(handle_vtb_support, Command("vtb_support", prefix="/"))

def register(dp: Dispatcher) -> None:
    """
    Регистрирует обработчик vtb_support через роутер.
    """
    dp.include_router(router)
