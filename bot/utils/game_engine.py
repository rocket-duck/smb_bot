import logging
import random
from datetime import UTC, datetime

from aiogram.utils.markdown import hlink
from sqlalchemy import select

from bot.database import SessionLocal
from bot.models import LastWinner, Participant, WinnerStats

logger = logging.getLogger(__name__)


async def update_last_winner(
    chat_id: str,
    chat_title: str,
    user_id: str,
    full_name: str,
    username: str,
) -> None:
    """Обновляет или создаёт запись о последнем победителе для заданного чата."""
    async with SessionLocal() as session:
        try:
            result = await session.execute(
                select(LastWinner).filter(LastWinner.chat_id == chat_id)
            )
            last = result.scalars().first()
            now = datetime.now(UTC)
            if last is None:
                last = LastWinner(
                    chat_id=chat_id,
                    chat_title=chat_title,
                    last_datetime=now,
                    winner_user_id=user_id,
                    winner_full_name=full_name,
                    winner_username=username or "",
                )
                session.add(last)
            else:
                last.chat_title = chat_title
                last.last_datetime = now
                last.winner_user_id = user_id
                last.winner_full_name = full_name
                last.winner_username = username or ""
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("Ошибка обновления последнего победителя: %s", e)
            raise


async def update_winner_stats(
    chat_id: str,
    chat_title: str,
    user_id: str,
    full_name: str,
    username: str,
) -> None:
    """Обновляет статистику побед для пользователя в заданном чате."""
    async with SessionLocal() as session:
        try:
            result = await session.execute(
                select(WinnerStats).filter(
                    WinnerStats.chat_id == chat_id, WinnerStats.user_id == user_id
                )
            )
            stats = result.scalars().first()
            if stats is None:
                stats = WinnerStats(
                    chat_id=chat_id,
                    chat_title=chat_title,
                    user_id=user_id,
                    full_name=full_name,
                    username=username or "",
                    wins=1,
                )
                session.add(stats)
            else:
                stats.wins += 1
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("Ошибка обновления статистики побед: %s", e)
            raise


async def get_last_winner(chat_id: str):
    """Возвращает запись о последнем победителе для заданного чата (или None)."""
    async with SessionLocal() as session:
        result = await session.execute(
            select(LastWinner).filter(LastWinner.chat_id == chat_id)
        )
        return result.scalars().first()


async def is_new_day(chat_id: str) -> bool:
    """Возвращает True, если текущая дата позже даты последнего выбора победителя."""
    last = await get_last_winner(chat_id)
    if not last:
        return True
    return datetime.now(UTC).date() > last.last_datetime.date()


async def get_random_participant(chat_id: str):
    """Возвращает случайного участника из таблицы участников для заданного чата."""
    async with SessionLocal() as session:
        result = await session.execute(
            select(Participant).filter(Participant.chat_id == chat_id)
        )
        participants = result.scalars().all()
    if participants:
        return random.choice(participants)
    return None


def format_declension(wins: int) -> str:
    """Возвращает правильную форму слова 'победа' в зависимости от числа wins."""
    if wins % 10 == 1 and wins % 100 != 11:
        return "победа"
    elif wins % 10 in [2, 3, 4] and wins % 100 not in [12, 13, 14]:
        return "победы"
    else:
        return "побед"


def format_winner_mention(user_id: str, full_name: str) -> str:
    """Формирует строку для упоминания пользователя."""
    return hlink(full_name, f"tg://user?id={user_id}")
