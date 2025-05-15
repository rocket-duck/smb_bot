import logging
from pathlib import Path
from aiogram.types import Message, FSInputFile


def contains_maslina(text: str) -> bool:
    """
    Проверяет, содержит ли текст слова "маслина"
    или "маслину" (без учета регистра).
    """
    lower_text = text.lower()
    return "маслина" in lower_text or "маслину" in lower_text


async def handle_maslina(message: Message, maslina_enable) -> bool:
    """
    Если сообщение содержит слова "маслина" или "маслину",
    отправляет картинку в виде реплая на это сообщение.
    Возвращает True, если картинка была отправлена, иначе False.
    """
    if not maslina_enable:
        return False

    if not message.text:
        return False
    if contains_maslina(message.text):
        # Определяем путь к картинке.
        base_dir = Path(__file__).resolve().parent.parent
        image_path = base_dir / "utils" / "img" / "maslina.jpeg"
        if not image_path.exists():
            logging.error(f"Картинка не найдена по пути: {image_path}")
            return False
        photo = FSInputFile(str(image_path))
        # Отправляем картинку реплаем на сообщение, содержащее ключевое слово.
        await message.reply_photo(photo=photo)
        return True
    return False
