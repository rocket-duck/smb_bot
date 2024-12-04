from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot.config.links import LINKS
from bot.menu.helpers import is_valid_url
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

def create_submenu(menu_key):
    """
    Создаёт подменю для указанного раздела.

    :param menu_key: Ключ раздела
    :return: InlineKeyboardMarkup с кнопками
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    if isinstance(LINKS.get(menu_key), dict):
        for sub_key, sub_value in LINKS[menu_key].items():
            if isinstance(sub_value, str):  # Если sub_value — строка, это URL
                url = sub_value
            elif isinstance(sub_value, dict):  # Если sub_value — словарь, извлекаем URL
                url = sub_value.get("url")
            else:
                logging.warning(f"Некорректное значение для {sub_key}: {sub_value}")
                continue

            # Проверяем URL
            if is_valid_url(url):
                keyboard.inline_keyboard.append([InlineKeyboardButton(text=sub_key, url=url)])
            else:
                logging.warning(f"Некорректный или отсутствующий URL для {sub_key}: {url}")

    # Добавляем кнопку "Назад"
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")])
    return keyboard