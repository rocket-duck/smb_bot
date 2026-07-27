import asyncio
import random

from aiogram import Bot
from aiogram.types import Message

from bot.config.flags import BEST_QA_ENABLE
from bot.utils.command_registry import command
from bot.utils.game_engine import (
    format_participant_list,
    format_winner_mention,
    get_last_winner,
    get_participants,
    is_new_day,
    update_last_winner,
    update_winner_stats,
)

SUSPENSE_SECONDS = 2


async def run_best_qa(bot: Bot, chat_id: int, chat_title: str) -> None:
    """Запускает выбор лучшего тестировщика дня в заданном чате."""
    if not await is_new_day(chat_id):
        last = await get_last_winner(chat_id)
        if last:
            mention = format_winner_mention(last.winner_user_id, last.winner_full_name)
            await bot.send_message(
                chat_id,
                f"Сегодня лучший тестировщик уже выбран: {mention} 🎉",
                parse_mode="HTML",
            )
        return

    participants = await get_participants(chat_id)
    if not participants:
        await bot.send_message(chat_id, "Не нашёл участников для выбора.")
        return

    await bot.send_message(chat_id, format_participant_list(participants))

    roll = random.randint(1, len(participants))
    await bot.send_message(chat_id, f"🎲 Бросаем кубик: 1d{len(participants)}...")
    await asyncio.sleep(SUSPENSE_SECONDS)

    winner = participants[roll - 1]
    await update_last_winner(
        chat_id, chat_title, winner.user_id, winner.full_name, winner.username
    )
    await update_winner_stats(
        chat_id, chat_title, winner.user_id, winner.full_name, winner.username
    )
    mention = format_winner_mention(winner.user_id, winner.full_name)
    await bot.send_message(
        chat_id, f"Сегодня лучший тестировщик {mention} 🎉", parse_mode="HTML"
    )


@command("best_qa", flag=BEST_QA_ENABLE)
async def handle_best_qa(message: Message) -> None:
    if message.chat.type == "private":
        await message.answer("Эта команда доступна только в групповых чатах.")
        return

    await run_best_qa(message.bot, message.chat.id, message.chat.title or "Личный чат")
