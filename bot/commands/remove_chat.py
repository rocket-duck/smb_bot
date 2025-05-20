import logging
import asyncio
import functools
from aiogram.filters import Command
from aiogram.types import Message
from aiogram import Router, Dispatcher
from bot.config.flags import REMOVE_CHAT_ENABLE
from bot.services.chat_service import remove_chat
from bot.services.admin_service import is_user_admin

logger = logging.getLogger(__name__)
router = Router()

@router.message.middleware()
async def check_flag(handler, event, data):
    if not REMOVE_CHAT_ENABLE:
        logger.debug("remove_chat disabled by flag")
        await event.delete()  # remove invocation even if disabled
        return
    return await handler(event, data)

def catch_exceptions(fn):
    @functools.wraps(fn)
    async def wrapper(message: Message, *args, **kwargs):
        try:
            await fn(message, *args, **kwargs)
        except Exception as e:
            logger.exception(f"Error in remove_chat handler: {e}")
            # ensure invocation message is deleted, no feedback to user
            try:
                await message.delete()
            except:
                pass
    return wrapper

@router.message(
    Command(commands=["remove_chat"], prefix="/"),
    lambda message: message.chat.type == "group"
)
@catch_exceptions
async def handle_remove_chat(message: Message) -> None:
    """
    /remove_chat: mark current group chat as removed (admins only).
    Does not send any messages, only deletes the invocation.
    """
    loop = asyncio.get_running_loop()
    # delete the invocation
    try:
        await message.delete()
    except Exception:
        pass
    # check admin permissions
    is_admin = await loop.run_in_executor(None, is_user_admin, message.from_user.id)
    if not is_admin:
        logger.debug(f"User {message.from_user.id} is not admin; skip")
        return
    # perform removal
    chat_id = message.chat.id
    removed_by = message.from_user.username or message.from_user.full_name or ""
    await loop.run_in_executor(None, remove_chat, chat_id, removed_by)
    logger.info(f"Marked chat {chat_id} as removed by {removed_by}")


def register(dp: Dispatcher) -> None:
    """
    Регистрирует обработчик /remove_chat через Router.
    """
    dp.include_router(router)
