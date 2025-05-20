import logging
from aiogram import Router, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from bot.services.best_qa_service import select_best_qa, AlreadyChosenToday, NoParticipants, format_winner_mention
from bot.config.flags import BEST_QA_ENABLE
from typing import Callable, Awaitable
import functools

logger = logging.getLogger(__name__)
router = Router()


def catch_exceptions(func: Callable[[Message], Awaitable[None]]) -> Callable[[Message], Awaitable[None]]:
    """
    Декоратор для перехвата непредвиденных ошибок в обработчике команд.
    """
    @functools.wraps(func)
    async def wrapper(message: Message) -> None:
        try:
            await func(message)
        except Exception as e:
            logger.exception(f"Unexpected error in {func.__name__}: {e}")
            await message.reply("Произошла внутренняя ошибка, попробуйте позже.")
    return wrapper


@catch_exceptions
async def handle_best_qa(message: Message) -> None:
    """
    Обработчик команды /best_qa: выбирает лучшего QA дня или сообщает статус.
    :param message: объект Telegram-сообщения
    :return: None
    """
    logger.info(f"Received /best_qa in chat {message.chat.id}")
    if not BEST_QA_ENABLE:
        logger.info("best_qa command is disabled")
        await message.answer("Команда временно отключена.")
        return
    if message.chat.type == "private":
        logger.info("best_qa command used in private chat")
        await message.answer("Эта команда доступна только в групповых чатах.")
        return

    chat_id = str(message.chat.id)
    chat_title = message.chat.title or "Личный чат"

    try:
        mention = await select_best_qa(chat_id, chat_title)
        logger.info(f"Best QA selected: {mention} in chat {chat_id}")
        await message.answer(f"Сегодня лучший тестировщик {mention} 🎉", parse_mode="HTML")
    except AlreadyChosenToday as e:
        last = e.last_winner
        mention = format_winner_mention(last.winner_user_id, last.winner_full_name)
        logger.info("Attempt to reselect best QA: already chosen")
        await message.answer(
            f"Сегодня лучший тестировщик уже выбран: {mention} 🎉",
            parse_mode="HTML"
        )
    except NoParticipants:
        logger.info(f"No participants to choose in chat {chat_id}")
        await message.answer("Не нашёл участников для выбора.")
    except Exception as e:
        logger.exception(f"Error during best_qa selection: {e}")
        await message.reply("Произошла ошибка при выборе лучшего тестировщика.")


router.message.register(handle_best_qa, Command(commands=["best_qa"]))


def register(dp: Dispatcher) -> None:
    """
    Регистрирует обработчик /best_qa через Router.
    """
    dp.include_router(router)
