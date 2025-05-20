import logging
import functools
import asyncio
from html import escape
from aiogram import Router, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from bot.services.commands_service import get_all_command_defs
from bot.services.admin_service import is_user_admin

_cached_get_command_defs = functools.lru_cache(maxsize=None)(get_all_command_defs)

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command(commands=["help"], prefix="/"))
async def handle_help(message: Message) -> None:
    """
    Отправляет список доступных команд, фильтруя по типу чата и правам пользователя.
    """
    logger.info(f"Received /help from user {message.from_user.id} in chat {message.chat.id}")
    loop = asyncio.get_running_loop()
    user_is_admin = await loop.run_in_executor(None, is_user_admin, message.from_user.id)
    logger.debug(f"User is_admin={user_is_admin}")

    # Get and cache command definitions
    all_defs = _cached_get_command_defs(user_is_admin=user_is_admin)
    # Determine chat attribute name
    scope_attr = "private_chat" if message.chat.type == "private" else "group_chat"
    # Filter definitions
    visible_defs = [
        cmd for cmd in all_defs
        if getattr(cmd, scope_attr) and cmd.visible_in_help
    ]
    logger.debug(
        f"Visible commands for {scope_attr} (admin={user_is_admin}): "
        f"{[cmd.command for cmd in visible_defs]}"
    )
    if not visible_defs:
        await message.answer("Нет доступных команд для вашего чата.")
        return
    # Build help text
    lines = ["Привет! Вот список доступных команд:", ""]
    for cmd in visible_defs:
        lines.append(f"/{cmd.command} — {escape(cmd.description)}")
    help_text = "\n".join(lines)
    await message.answer(help_text)


def register(dp: Dispatcher) -> None:
    """
    Регистрирует обработчик /help через Router.
    """
    dp.include_router(router)
