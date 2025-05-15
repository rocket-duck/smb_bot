from aiogram import types
from pathlib import Path
from aiogram.types import FSInputFile

BASE_DIR = Path(__file__).resolve().parent.parent
IMG_DIR = BASE_DIR / "utils" / "img"


def normalize_bot_username(bot_username: str) -> str:
    """
    Если bot_username передан как кортеж, возвращает первый элемент.
    Иначе возвращает строку.
    """
    if isinstance(bot_username, tuple):
        return bot_username[0]
    return bot_username


def is_bot_mentioned(message: types.Message, bot_username: str) -> bool:
    """
    Проверяет, упоминается ли бот в сообщении.
    :param message: Объект сообщения
    :param bot_username: Имя бота (строка без символа '@')
    :return: True, если сообщение содержит упоминание бота, иначе False.
    """
    if not message.entities:
        return False

    normalized_username = bot_username.lower()
    for entity in message.entities:
        if entity.type == "mention":
            mention_text = message.text[
                entity.offset: entity.offset + entity.length
            ]
            if mention_text.lower() == f"@{normalized_username}":
                return True
    return False


async def handle_bot_tag(message: types.Message,
                         bot_username: str,
                         bot_tag_enable: bool) -> None:
    """
    Если сообщение содержит упоминание бота
    (например, @bot_username) и включена обработка тегов,
    отправляет видео из каталога img/wait.mov.

    :param message: Объект сообщения.
    :param bot_username: Имя бота без '@'.
    Если передан кортеж, используется первый элемент.
    :param bot_tag_enable: Флаг, разрешающий обработку тега бота.
    """
    if not bot_tag_enable:
        return

    bot_username = normalize_bot_username(bot_username)

    if is_bot_mentioned(message, bot_username):
        video_path = IMG_DIR / "wait.mov"
        if video_path.exists():
            video_file = FSInputFile(str(video_path))
            await message.answer_video(video=video_file)
        else:
            await message.answer("Видео не найдено.")
