from aiogram.types import Message

from bot.config.flags import DUSHNILA_WHY_ENABLE
from bot.models import DushnilaEvent
from bot.utils.command_registry import command
from bot.utils.dushnila_engine import find_participant_by_username, get_today_events

EVENTS_LIMIT = 10


def format_why(full_name: str, events: list[DushnilaEvent]) -> str:
    """Форматирует список последних начислений баллов душности за сегодня."""
    lines = [f"🔥 {full_name} сегодня:"]
    for event in events:
        sign = "+" if event.points >= 0 else ""
        lines.append(f"{sign}{event.points} за {event.reason}")
    return "\n".join(lines)


@command("dushnila_why", flag=DUSHNILA_WHY_ENABLE)
async def handle_dushnila_why(message: Message) -> None:
    if message.chat.type == "private":
        await message.answer("Эта команда доступна только в групповых чатах.")
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer("Использование: /dushnila_why @username")
        return

    username = parts[1].strip()
    participant = await find_participant_by_username(message.chat.id, username)
    if not participant:
        await message.answer(f"Не нашёл участника {username} в этом чате.")
        return

    events = await get_today_events(
        message.chat.id, participant.user_id, limit=EVENTS_LIMIT
    )
    if not events:
        await message.answer(
            f"У {participant.full_name} сегодня пока нет баллов душности."
        )
        return

    await message.answer(format_why(participant.full_name, events))
