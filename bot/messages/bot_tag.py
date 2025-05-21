from aiogram import types
from pathlib import Path
from aiogram.types import FSInputFile
import logging

from bot.config.tokens import BOT_USERNAME

BASE_DIR = Path(__file__).resolve().parent.parent
IMG_DIR = BASE_DIR / "utils" / "img"

logger = logging.getLogger(__name__)


def is_bot_mentioned(message: types.Message) -> bool:
    """
    Проверяет, упоминается ли бот в сообщении.
    Username берется из глобальной переменной BOT_USERNAME.
    """
    if not getattr(message, "text", None) or not message.entities:
        return False

    if not BOT_USERNAME:
        logger.error("BOT_USERNAME is not set in bot_tag.py!")
        return False

    normalized_username = BOT_USERNAME.lower()
    for entity in message.entities:
        if entity.type == "mention":
            mention_text = message.text[entity.offset : entity.offset + entity.length]
            if mention_text.lower() == f"@{normalized_username}":
                logger.info("Bot mention detected")
                return True
    return False


async def handle_bot_tag(message: types.Message, bot_tag_enable: bool) -> bool:
    """
    Если сообщение содержит упоминание бота (например, @bot_username) и включена обработка тегов,
    отправляет видео из каталога img/wait.mov.
    Возвращает True если сообщение обработано (чтобы можно было прервать дальнейшую обработку).
    """
    if not bot_tag_enable:
        return False

    if not BOT_USERNAME:
        logger.error("BOT_USERNAME is not set in bot_tag.py!")
        return False

    if is_bot_mentioned(message):
        video_path = IMG_DIR / "wait.mov"
        if video_path.exists():
            video_file = FSInputFile(str(video_path))
            await message.answer_video(video=video_file)
            logger.info("Video sent in response to bot mention")
            return True
        else:
            logger.warning("Video file not found at path: %s", video_path)
            await message.answer("Видео не найдено.")
            return True
    return False
