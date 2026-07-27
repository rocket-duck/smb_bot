from aiogram.types import Message

from bot.config.flags import DUSHNILA_WEEKLY_ENABLE
from bot.utils.command_registry import command
from bot.utils.dushnila_engine import (
    format_display_name,
    format_points_declension,
    get_weekly_totals,
    level_for_score,
)

TOP_LIMIT = 10


def format_weekly_top(totals: list[tuple[int, str, str, int]]) -> str:
    """Форматирует топ душнил недели."""
    lines = ["🏆 Топ душнил недели"]
    for rank, (_, full_name, username, total) in enumerate(totals[:TOP_LIMIT], start=1):
        name = format_display_name(full_name, username)
        declension = format_points_declension(total)
        level = level_for_score(total)
        lines.append(f"{rank}. {name} — {total} {declension} {level}")
    return "\n".join(lines)


@command("dushnila_weekly", flag=DUSHNILA_WEEKLY_ENABLE)
async def handle_dushnila_weekly(message: Message) -> None:
    if message.chat.type == "private":
        await message.answer("Эта команда доступна только в групповых чатах.")
        return

    totals = await get_weekly_totals(message.chat.id)
    if not totals:
        await message.answer("На этой неделе пока нет активности душнил.")
        return

    await message.answer(format_weekly_top(totals))
