import logging

from aiogram.types import Message

from bot.config.flags import DUSHNILA_RESET_WEEK_ENABLE
from bot.utils.command_registry import command
from bot.utils.dushnila_engine import reset_week

ADMIN_STATUSES = {"administrator", "creator"}


async def is_chat_admin(message: Message) -> bool:
    try:
        member = await message.bot.get_chat_member(
            message.chat.id, message.from_user.id
        )
        return member.status in ADMIN_STATUSES
    except Exception as exc:  # noqa: BLE001
        logging.warning("Не удалось проверить права администратора: %s", exc)
        return False


@command("dushnila_reset_week", flag=DUSHNILA_RESET_WEEK_ENABLE)
async def handle_dushnila_reset_week(message: Message) -> None:
    if message.chat.type == "private":
        await message.answer("Эта команда доступна только в групповых чатах.")
        return

    if not await is_chat_admin(message):
        await message.answer(
            "Сбросить недельный рейтинг может только администратор чата."
        )
        return

    await reset_week(message.chat.id)
    await message.answer("Недельный рейтинг душнил сброшен.")
