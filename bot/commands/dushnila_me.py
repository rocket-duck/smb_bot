from aiogram.types import Message

from bot.config.flags import DUSHNILA_ME_ENABLE
from bot.utils.command_registry import command
from bot.utils.dushnila_engine import (
    format_points_declension,
    get_personal_weekly_total,
    level_for_score,
)


@command("dushnila_me", flag=DUSHNILA_ME_ENABLE)
async def handle_dushnila_me(message: Message) -> None:
    if message.chat.type == "private":
        await message.answer("Эта команда доступна только в групповых чатах.")
        return

    total = await get_personal_weekly_total(message.chat.id, message.from_user.id)
    declension = format_points_declension(total)
    level = level_for_score(total)
    await message.answer(f"Твой результат за неделю: {total} {declension} {level}")
