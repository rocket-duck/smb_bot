import logging
from aiogram.types import Message, FSInputFile
from pathlib import Path

# Путь к папке с изображениями
BASE_DIR = Path(__file__).resolve().parent.parent
IMG_DIR = BASE_DIR / "utils" / "img"

# Триггерные фразы
TRIGGERS = ["а кто",
            "а почему",
            "а когда",
            "а где",
            "а как"]


async def handle_who_request(message: Message,
                             who_request_enable: bool):
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

    # Проверяем, начинается ли сообщение с одной из триггерных фраз
    message_text = message.text.lower()
    if not any(message_text.startswith(trigger) for trigger in TRIGGERS):
        return

    logging.debug(f"Обнаружен запрос '{message_text}' "
                  f"с одним из триггеров: {TRIGGERS}")

    # Путь к конкретному изображению
    image_path = IMG_DIR / "a_kto_cenz.png"
    if not image_path.exists():
        logging.warning(f"Изображение '{image_path}' не найдено.")
        return

    logging.debug(f"Отправка изображения: {image_path}")

    # Создаем объект FSInputFile с указанием пути к файлу
    photo = FSInputFile(image_path)

    # Отправляем изображение
    await message.answer_photo(photo=photo,
                               reply_to_message_id=message.message_id)
