import logging
from aiogram.filters import Command
from aiogram.types import Message
from bot.config.flags import BEST_QA_STAT_ENABLE
from bot.database import SessionLocal
from bot.models import WinnerStats
from bot.utils.game_engine import format_declension

logging.basicConfig(level=logging.DEBUG)


def get_stats(chat_id: str) -> list:
    """
    Получает статистику победителей для заданного чата из базы данных,
    сортируя записи по количеству побед (от большего к меньшему).
    """
    session = SessionLocal()
    try:
        stats = session.query(WinnerStats) \
            .filter(WinnerStats.chat_id == chat_id) \
            .order_by(WinnerStats.wins.desc()) \
            .all()
        return stats
    except Exception as e:
        logging.error("Ошибка получения статистики: %s", e)
        return []
    finally:
        session.close()


def format_stats(message: Message, stats: list) -> str:
    """
    Форматирует статистику победителей в строку для отправки пользователю.
    """
    chat_title = stats[0].chat_title if stats[0].chat_title \
        else message.chat.title
    stat_lines = [f"Статистика победителей для чата: {chat_title}:"]
    for stat in stats:
        username = f" (@{stat.username})" if stat.username else ""
        declension = format_declension(stat.wins)
        stat_lines.append(f"• {stat.full_name}{username}: "
                          f"{stat.wins} {declension}")
    return "\n".join(stat_lines)


async def handle_best_qa_stat(message: Message) -> None:
    if not BEST_QA_STAT_ENABLE:
        await message.answer("Команда временно отключена.")
        return
    if message.chat.type == "private":
        await message.answer("Статистика доступна только для групповых чатов.")
        return

    chat_id = str(message.chat.id)
    stats = get_stats(chat_id)
    if not stats:
        await message.answer("Статистика по лучшим тестировщикам пока пуста.")
        return

    help_text = format_stats(message, stats)
    await message.answer(help_text)


def register_best_qa_stat_handler(dp) -> None:
    dp.message.register(handle_best_qa_stat,
                        Command(commands=["best_qa_stat"]))
