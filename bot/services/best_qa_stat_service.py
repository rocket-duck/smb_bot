import logging
from typing import List
from bot.database import SessionLocal
from bot.models import WinnerStats

logger = logging.getLogger(__name__)

class StatsServiceError(Exception):
    """Базовое исключение для сервиса статистики."""

async def get_stats(chat_id: str) -> List[WinnerStats]:
    """
    Получает список WinnerStats по chat_id, отсортированный по wins desc.
    :raises StatsServiceError: при ошибке доступа к БД.
    """
    session = SessionLocal()
    try:
        stats = (
            session.query(WinnerStats)
            .filter(WinnerStats.chat_id == chat_id)
            .order_by(WinnerStats.wins.desc())
            .all()
        )
        return stats
    except Exception as e:
        logger.error("Ошибка получения статистики: %s", e)
        raise StatsServiceError from e
    finally:
        session.close()

def format_stats_text(stats: List[WinnerStats], chat_title: str) -> str:
    """
    Форматирует результаты stats в текст для отправки.
    """
    title = chat_title or (stats[0].chat_title if stats else "Чат")
    lines = [f"📊 Статистика победителей для чата: {title}:"]
    for st in stats:
        user_part = f" (@{st.username})" if st.username else ""
        decl = format_declension(st.wins)
        lines.append(f"• {st.full_name}{user_part}: {st.wins} {decl}")
    return "\n".join(lines)


def format_declension(wins: int) -> str:
    """Формирует склонение слова 'победа' по количеству побед."""
    if wins % 10 == 1 and wins % 100 != 11:
        return "победа"
    if wins % 10 in [2, 3, 4] and wins % 100 not in [12, 13, 14]:
        return "победы"
    return "побед"