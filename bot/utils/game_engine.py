import random
import logging
from datetime import datetime, timezone
from aiogram.utils.markdown import hlink

from bot.database import SessionLocal
from bot.models import LastWinner, WinnerStats, Participant

logger = logging.getLogger(__name__)


def update_last_winner(chat_id: str,
                       chat_title: str,
                       user_id: str,
                       full_name: str,
                       username: str) -> None:
    """Обновляет или создаёт запись о последнем
    победителе для заданного чата."""
    session = SessionLocal()
    try:
        last = (session.query(LastWinner)
                .filter(LastWinner.chat_id == chat_id).first())
        now = datetime.now(timezone.utc)
        if last is None:
            last = LastWinner(
                chat_id=chat_id,
                chat_title=chat_title,
                last_datetime=now,
                winner_user_id=user_id,
                winner_full_name=full_name,
                winner_username=username or ""
            )
            session.add(last)
        else:
            last.chat_title = chat_title
            last.last_datetime = now
            last.winner_user_id = user_id
            last.winner_full_name = full_name
            last.winner_username = username or ""
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error("Ошибка обновления последнего победителя: %s", e)
        raise
    finally:
        session.close()


def update_winner_stats(chat_id: str,
                        chat_title: str,
                        user_id: str,
                        full_name: str,
                        username: str) -> None:
    """Обновляет статистику побед для пользователя в заданном чате."""
    session = SessionLocal()
    try:
        stats = session.query(WinnerStats).filter(
            WinnerStats.chat_id == chat_id,
            WinnerStats.user_id == user_id
        ).first()
        if stats is None:
            stats = WinnerStats(
                chat_id=chat_id,
                chat_title=chat_title,
                user_id=user_id,
                full_name=full_name,
                username=username or "",
                wins=1
            )
            session.add(stats)
        else:
            stats.wins += 1
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error("Ошибка обновления статистики побед: %s", e)
        raise
    finally:
        session.close()


def get_last_winner(chat_id: str):
    """Возвращает запись о последнем победителе
    для заданного чата (или None)."""
    session = SessionLocal()
    try:
        return (session.query(LastWinner)
                .filter(LastWinner.chat_id == chat_id).first())
    finally:
        session.close()


def is_new_day(chat_id: str) -> bool:
    """Возвращает True, если текущая дата позже
    даты последнего выбора победителя."""
    last = get_last_winner(chat_id)
    if not last:
        return True
    return datetime.now(timezone.utc).date() > last.last_datetime.date()
    # return True


def get_random_participant(chat_id: str):
    """Возвращает случайного участника из таблицы
    участников для заданного чата."""
    session = SessionLocal()
    try:
        participants = (session.query(Participant)
                        .filter(Participant.chat_id == chat_id).all())
    finally:
        session.close()
    if participants:
        return random.choice(participants)
    return None


def format_declension(wins: int) -> str:
    """Возвращает правильную форму слова 'победа'
    в зависимости от числа wins."""
    if wins % 10 == 1 and wins % 100 != 11:
        return "победа"
    elif wins % 10 in [2, 3, 4] and not (wins % 100 in [12, 13, 14]):
        return "победы"
    else:
        return "побед"


def format_winner_mention(user_id: str, full_name: str) -> str:
    """Формирует строку для упоминания пользователя."""
    return hlink(full_name, f"tg://user?id={user_id}")
