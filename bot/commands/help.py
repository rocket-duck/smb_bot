import logging
from aiogram.types import Message

from bot.config.flags import HELP_ENABLE
from bot.modules.commands_list import get_all_commands
from bot.utils.admins import is_user_admin_db
from bot.utils.command_registry import command

logger = logging.getLogger(__name__)


@command("help", flag=HELP_ENABLE)
async def handle_help(message: Message):
    """Обрабатывает команду /help."""
    user_is_admin = await is_user_admin_db(message.from_user.id)
    commands = get_all_commands(user_is_admin=user_is_admin)
    logger.debug("Все команды: %s", commands)

    chat_type = "private_chat" if message.chat.type == "private" else "group_chat"
    visible_commands = [
        cmd["command"]
        for cmd in commands
        if cmd.get(chat_type) and cmd.get("visible_in_help", True)
    ]
    logger.debug(
        "Доступные команды для %s (admin=%s): %s",
        chat_type,
        user_is_admin,
        visible_commands,
    )

    if not visible_commands:
        await message.answer("Нет доступных команд для вашего чата.")
        return

    help_text = "Привет! Вот список доступных команд:\n\n"
    for cmd in visible_commands:
        help_text += f"/{cmd.command} — {cmd.description}\n"

    await message.answer(help_text)
