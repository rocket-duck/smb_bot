from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot.config.links import LINKS
from bot.menu.helpers import is_valid_url
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

def create_main_menu():
    """
    Создаёт главное меню с кнопками для каждого раздела в LINKS.

    :return: InlineKeyboardMarkup с кнопками
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for section, content in LINKS.items():
        # Если content — строка, предполагаем, что это URL
        if isinstance(content, str):
            url = content
        # Если content — словарь, извлекаем URL
        elif isinstance(content, dict):
            url = content.get("url")
        else:
            logging.warning(f"Некорректное значение для раздела {section}: {content}")
            continue

        # Добавляем кнопки
        if is_valid_url(url):
            keyboard.inline_keyboard.append([InlineKeyboardButton(text=section.capitalize(), url=url)])
        else:
            keyboard.inline_keyboard.append(
                [InlineKeyboardButton(text=section.capitalize(), callback_data=f"menu:{section}")]
            )

    return keyboard
