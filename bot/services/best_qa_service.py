import logging
import random
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
    """Обновляет или создаёт запись о последнем победителе для чата."""
    session = SessionLocal()
    try:
        last = session.query(LastWinner).filter(
            LastWinner.chat_id == chat_id
        ).first()
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
    except Exception:
        session.rollback()
        logger.exception("Ошибка обновления последнего победителя")
        raise
    finally:
        session.close()

def update_winner_stats(chat_id: str,
                        chat_title: str,
                        user_id: str,
                        full_name: str,
                        username: str) -> None:
    """Обновляет статистику побед для пользователя в чате."""
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
    except Exception:
        session.rollback()
        logger.exception("Ошибка обновления статистики побед")
        raise
    finally:
        session.close()

def get_last_winner(chat_id: str):
    """Возвращает запись о последнем победителе для чата."""
    session = SessionLocal()
    try:
        return session.query(LastWinner).filter(
            LastWinner.chat_id == chat_id
        ).first()
    finally:
        session.close()

def is_new_day(chat_id: str) -> bool:
    """True, если сегодня день позже последнего выбора победителя."""
    last = get_last_winner(chat_id)
    if not last:
        return True
    return datetime.now(timezone.utc).date() > last.last_datetime.date()

def get_random_participant(chat_id: str):
    """Возвращает случайного участника из таблицы участников."""
    session = SessionLocal()
    try:
        participants = session.query(Participant).filter(
            Participant.chat_id == chat_id
        ).all()
    finally:
        session.close()
    if participants:
        return random.choice(participants)
    return None



class BestQAServiceError(Exception):
    """Base exception for best_qa service."""

class AlreadyChosenToday(BestQAServiceError):
    """Raised if a winner was already chosen today."""
    def __init__(self, last_winner):
        super().__init__("Winner already chosen today")
        self.last_winner = last_winner

class NoParticipants(BestQAServiceError):
    """Raised if there are no participants to choose from."""

async def select_best_qa(chat_id: str, chat_title: str) -> str:
    """
    Selects and records the best QA for today.
    :param chat_id: identifier of the chat
    :param chat_title: display title of the chat
    :return: mention string of the selected participant
    :raises AlreadyChosenToday: if a winner was already chosen today
    :raises NoParticipants: if there are no participants to choose
    """
    # Check if already chosen today

    if not is_new_day(chat_id):
        last = get_last_winner(chat_id)
        if last:
            logger.info(f"Best QA already chosen today: {last.winner_user_id}")
            raise AlreadyChosenToday(last)

    # Select a new participant
    participant = get_random_participant(chat_id)
    if not participant:
        logger.warning(f"No participants found for chat {chat_id}")
        raise NoParticipants()

    # Record the winner
    update_last_winner(
        chat_id,
        chat_title,
        str(participant.user_id),
        participant.full_name,
        participant.username,
    )
    update_winner_stats(
        chat_id,
        chat_title,
        str(participant.user_id),
        participant.full_name,
        participant.username,
    )

    mention = format_winner_mention(participant.user_id, participant.full_name)
    logger.info(f"Selected new best QA: {participant.user_id} for chat {chat_id}")
    return mention

def format_winner_mention(user_id: str, full_name: str) -> str:
    """
    Формирует HTML-упоминание пользователя.
    """
    # Создаёт ссылку вида <a href="tg://user?id=...">Имя</a>
    return hlink(full_name, f"tg://user?id={user_id}")