import logging
from datetime import UTC, datetime

from sqlalchemy import select

from bot.database import SessionLocal
from bot.models import Participant


def _now_utc():
    """
    Возвращает текущее время в UTC.

    При монкипатчинге datetime (в тестах) используем utcnow() как fallback.
    """
    now_attr = getattr(datetime, "now", None)
    if callable(now_attr):
        return now_attr(UTC)
    return datetime.utcnow()


async def update_participant(message) -> None:
    # Если сообщение пришло из личного чата, не добавляем участника
    if message.chat.type == "private":
        logging.debug(
            "Сообщение из личного чата: участник не добавляется в таблицу."
        )
        return

    user = message.from_user
    chat_id = str(message.chat.id)
    async with SessionLocal() as session:
        try:
            result = await session.execute(
                select(Participant).filter(
                    Participant.chat_id == chat_id,
                    Participant.user_id == str(user.id),
                )
            )
            participant = result.scalars().first()

            if participant is None:
                # Создаем новую запись для участника с названием чата
                participant = Participant(
                    chat_id=chat_id,
                    user_id=str(user.id),
                    full_name=user.full_name,
                    username=user.username or "",
                    chat_title=message.chat.title or "",
                    last_active=_now_utc(),
                )
                session.add(participant)
                await session.commit()
                logging.info(
                    f"Добавлен новый участник: {user.full_name} (ID: {user.id}) в чат {chat_id}"
                )
            else:
                # Обновляем время последней активности и название чата (на случай, если оно изменилось)
                participant.last_active = _now_utc()
                participant.chat_title = message.chat.title or ""
                await session.commit()
                logging.debug(
                    f"Обновлена активность участника: {user.full_name} (ID: {user.id}) в чат {chat_id}"
                )
        except Exception as e:
            await session.rollback()
            logging.error(f"Ошибка при обновлении участника: {e}")
