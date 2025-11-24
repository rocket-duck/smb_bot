import logging
import re
from aiogram.types import Message, FSInputFile
from pathlib import Path
from bot.dicts import who_request_dict

# Путь к папке с изображениями
BASE_DIR = Path(__file__).resolve().parent.parent
IMG_DIR = BASE_DIR / "utils" / "img"


async def handle_who_request(message: Message,
                             who_request_enable: bool,
                             force_loh_image: bool = False):
    """
    Обрабатывает сообщения, начинающиеся с заданных фраз.
    Если сообщение соответствует, отправляет фиксированное изображение в ответ.
    :param message: Сообщение от пользователя
    :param who_request_enable: Флаг, разрешающий выполнение функции.
    """
    if not who_request_enable:
        return

    # Проверяем, есть ли текст в сообщении
    if not message.text:
        logging.debug("Сообщение не содержит текста. Пропускаем обработку.")
        return

    # Проверяем, содержит ли сообщение одну из триггерных фраз как отдельное слово/фразу
    message_text = message.text.lower()
    if not any(re.search(rf"\b{re.escape(trigger)}\b", message_text) for trigger in who_request_dict.TRIGGERS):
        return

    logging.debug(f"Обнаружен запрос '{message_text}' "
                  f"с одним из триггеров: {who_request_dict.TRIGGERS}")

    image_name = "loh.jpg" if force_loh_image else "a_kto_cenz.png"
    image_path = IMG_DIR / image_name
    if not image_path.exists():
        logging.warning(f"Изображение '{image_path}' не найдено.")
        return

    logging.debug(f"Отправка изображения: {image_path}")

    # Создаем объект FSInputFile с указанием пути к файлу
    photo = FSInputFile(image_path)

    # Отправляем изображение
    await message.answer_photo(photo=photo,
                               reply_to_message_id=message.message_id)
