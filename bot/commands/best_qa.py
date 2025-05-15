from aiogram.filters import Command
from aiogram.types import Message
from bot.config.flags import BEST_QA_ENABLE
from bot.utils.game_engine import (
    update_last_winner,
    update_winner_stats,
    get_random_participant,
    is_new_day,
    format_winner_mention,
    get_last_winner
)


async def handle_best_qa(message: Message) -> None:
    if not BEST_QA_ENABLE:
        await message.answer("Команда временно отключена.")
        return
    if message.chat.type == "private":
        await message.answer("Эта команда доступна только в групповых чатах.")
        return

    chat_id = str(message.chat.id)
    # Если уже выбран победитель сегодня, уведомляем об этом
    if not is_new_day(chat_id):
        last = get_last_winner(chat_id)
        if last:
            mention = format_winner_mention(last.winner_user_id,
                                            last.winner_full_name)
            await message.answer(f"Сегодня лучший тестировщик "
                                 f"уже выбран: {mention} 🎉",
                                 parse_mode="HTML")
        return

    participant = get_random_participant(chat_id)
    if not participant:
        await message.answer("Не нашёл участников для выбора.")
        return

    update_last_winner(
        chat_id,
        message.chat.title or "Личный чат",
        str(participant.user_id),
        participant.full_name,
        participant.username
    )
    update_winner_stats(
        chat_id,
        message.chat.title or "Личный чат",
        str(participant.user_id),
        participant.full_name,
        participant.username
    )
    mention = format_winner_mention(participant.user_id, participant.full_name)
    await message.answer(f"Сегодня лучший тестировщик {mention} 🎉",
                         parse_mode="HTML")


def register_best_qa_handler(dp) -> None:
    dp.message.register(handle_best_qa, Command(commands=["best_qa"]))
