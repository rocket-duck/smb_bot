import logging
from aiogram.types import Message
from sqlalchemy import select

from bot.config.flags import BEST_QA_STAT_ENABLE
from bot.database import SessionLocal
from bot.models import WinnerStats
from bot.utils.command_registry import command
from bot.utils.game_engine import format_declension


async def get_stats(chat_id: str) -> list:
    """Получает статистику победителей для заданного чата."""
    async with SessionLocal() as session:
        try:
            result = await session.execute(
                select(WinnerStats)
                .filter(WinnerStats.chat_id == chat_id)
                .order_by(WinnerStats.wins.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logging.error("Ошибка получения статистики: %s", e)
            return []


def format_stats(message: Message, stats: list) -> str:
    """Форматирует статистику победителей."""
    chat_title = stats[0].chat_title if stats[0].chat_title else message.chat.title
    stat_lines = [f"Статистика победителей для чата: {chat_title}:"]
    for stat in stats:
        username = f" (@{stat.username})" if stat.username else ""
        declension = format_declension(stat.wins)
        stat_lines.append(
            f"• {stat.full_name}{username}: {stat.wins} {declension}"
        )
    return "\n".join(stat_lines)


@command("best_qa_stat", flag=BEST_QA_STAT_ENABLE)
async def handle_best_qa_stat(message: Message) -> None:
    if message.chat.type == "private":
        await message.answer("Статистика доступна только для групповых чатов.")
        return

    chat_id = str(message.chat.id)
    stats = await get_stats(chat_id)
    if not stats:
        await message.answer("Статистика по лучшим тестировщикам пока пуста.")
        return

    help_text = format_stats(message, stats)
    await message.answer(help_text)
