from aiogram.types import Message

from bot.config.flags import BEST_QA_ENABLE
from bot.utils.command_registry import command
from bot.utils.game_engine import (
    format_winner_mention,
    get_last_winner,
    get_random_participant,
    is_new_day,
    update_last_winner,
    update_winner_stats,
)


@command("best_qa", flag=BEST_QA_ENABLE)
async def handle_best_qa(message: Message) -> None:
    if message.chat.type == "private":
        await message.answer("Эта команда доступна только в групповых чатах.")
        return

    chat_id = str(message.chat.id)
    if not await is_new_day(chat_id):
        last = await get_last_winner(chat_id)
        if last:
            mention = format_winner_mention(last.winner_user_id, last.winner_full_name)
            await message.answer(
                f"Сегодня лучший тестировщик уже выбран: {mention} 🎉",
                parse_mode="HTML",
            )
        return

    participant = await get_random_participant(chat_id)
    if not participant:
        await message.answer("Не нашёл участников для выбора.")
        return

    await update_last_winner(
        chat_id,
        message.chat.title or "Личный чат",
        str(participant.user_id),
        participant.full_name,
        participant.username,
    )
    await update_winner_stats(
        chat_id,
        message.chat.title or "Личный чат",
        str(participant.user_id),
        participant.full_name,
        participant.username,
    )
    mention = format_winner_mention(participant.user_id, participant.full_name)
    await message.answer(
        f"Сегодня лучший тестировщик {mention} 🎉",
        parse_mode="HTML",
    )
