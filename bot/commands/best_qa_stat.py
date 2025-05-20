import logging
from aiogram import Router, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from bot.config.flags import BEST_QA_STAT_ENABLE
from bot.services.best_qa_stat_service import get_stats, format_stats_text, StatsServiceError
from typing import Callable, Awaitable

logger = logging.getLogger(__name__)
router = Router()

@router.message.middleware()
async def check_enabled(handler, event, data):
    """
    Middleware: blocks handler if BEST_QA_STAT_ENABLE is False.
    """
    if not BEST_QA_STAT_ENABLE:
        await event.answer("Команда временно отключена.")
        return
    return await handler(event, data)

def catch_errors(func: Callable[[Message], Awaitable[None]]) -> Callable[[Message], Awaitable[None]]:
    """
    Decorator to catch and respond to errors in handler.
    """
    async def wrapper(message: Message) -> None:
        try:
            await func(message)
        except StatsServiceError:
            logger.error("StatsServiceError in best_qa_stat")
            await message.answer("Не удалось получить статистику. Попробуйте позже.")
        except Exception as e:
            logger.exception(f"Unexpected error in best_qa_stat: {e}")
            await message.answer("Произошла внутренняя ошибка.")
    return wrapper

@catch_errors
@router.message(Command(commands=["best_qa_stat"]))
async def handle_best_qa_stat(message: Message) -> None:
    """
    Обработчик команды /best_qa_stat: выводит статистику победителей чата.
    """
    logger.info(f"Received /best_qa_stat in chat {message.chat.id}")

    if message.chat.type == "private":
        logger.info("best_qa_stat used in private chat")
        await message.answer("Статистика доступна только для групповых чатах.")
        return

    chat_id = str(message.chat.id)
    chat_title = message.chat.title or ""

    stats = await get_stats(chat_id)
    if not stats:
        logger.info(f"No stats for chat {chat_id}")
        await message.answer("Статистика по лучшим тестировщикам пока пуста.")
        return

    # Limit to top 10 entries
    top_stats = stats[:10]
    logger.info(f"Formatting {len(top_stats)} stats entries for chat {chat_id}")
    text = format_stats_text(top_stats, chat_title)
    await message.answer(text)

def register(dp: Dispatcher) -> None:
    """
    Регистрирует обработчик /best_qa_stat через Router.
    """
    dp.include_router(router)
