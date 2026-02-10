import logging
import re
from pathlib import Path

from aiogram.types import FSInputFile, Message

from bot.config.settings import get_settings
from bot.dicts import who_request_dict

# Путь к папке с изображениями
BASE_DIR = Path(__file__).resolve().parent.parent
IMG_DIR = BASE_DIR / "utils" / "img"


async def handle_who_request(
    message: Message,
    who_request_enable: bool,
    force_image_name: str | None = None,
    user_roll: int | None = None,
    bot_roll: int | None = None,
) -> bool:
    """
    Обрабатывает сообщения, начинающиеся с заданных фраз.
    Если сообщение соответствует, отправляет фиксированное изображение в ответ.
    :param message: Сообщение от пользователя
    :param who_request_enable: Флаг, разрешающий выполнение функции.
    :return: True, если изображение было отправлено.
    """
    if not who_request_enable:
        return False
    settings = get_settings()
    if not settings.nfsw_chat_ids:
        return False
    if message.chat and message.chat.id not in settings.nfsw_chat_ids:
        return False

    # Проверяем, есть ли текст в сообщении
    if not message.text:
        logging.debug("Сообщение не содержит текста. Пропускаем обработку.")
        return False

    message_text = message.text.lower()
    if not is_who_request_trigger(message_text):
        return False

    logging.debug(
        f"Обнаружен запрос '{message_text}' "
        f"с одним из триггеров: {who_request_dict.TRIGGERS}"
    )

    image_name = force_image_name or "a_kto.jpg"
    image_path = IMG_DIR / image_name
    if not image_path.exists():
        logging.warning(f"Изображение '{image_path}' не найдено.")
        return False

    logging.debug(f"Отправка изображения: {image_path}")

    # Создаем объект FSInputFile с указанием пути к файлу
    photo = FSInputFile(image_path)

    # Отправляем изображение
    caption = None
    if user_roll is not None and bot_roll is not None:
        caption = f"roll 1d20\nUser roll: {user_roll}\nBot roll: {bot_roll}"
    await message.answer_photo(
        photo=photo, caption=caption, reply_to_message_id=message.message_id
    )
    return True


def is_who_request_trigger(text: str) -> bool:
    return any(
        re.search(rf"\b{re.escape(trigger)}\b", text)
        for trigger in who_request_dict.TRIGGERS
    )
