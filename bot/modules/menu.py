from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot.config.links import LINKS
import logging


def create_main_menu(user_id: int):
    """
    Создаёт главное меню на основе LINKS.
    :param user_id: ID пользователя (для уникальных callback_data)
    :return: Tuple (InlineKeyboardMarkup с кнопками, название меню)
    """
    if user_id is None:
        raise ValueError("user_id не должен быть None")
    logging.debug(f"Создание главного меню. user_id={user_id}")

    buttons = []
    for section, content in LINKS.items():
        url = content.get("url")
        subsections = content.get("subsections")
        key = content.get("key")
        if not subsections and url:
            # Если нет подразделов, но есть ссылка – создаём кнопку с ссылкой
            buttons.append([InlineKeyboardButton(text=section, url=url)])
        elif key:
            # Если есть ключ (в том числе с подразделами) –
            # создаём кнопку с callback_data
            callback_data = f"menu:{user_id}:{key}"
            buttons.append([InlineKeyboardButton(text=section,
                                                 callback_data=callback_data)])
        else:
            logging.warning(f"Пропущен раздел '{section}' "
                            f"из-за некорректной структуры.")
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard, "Главное меню"


def create_submenu(menu_key: str, user_id: int):
    """
    Создаёт подменю для указанного раздела.
    :param menu_key: Ключ раздела
    :param user_id: ID пользователя (для уникальных callback_data)
    :return: Tuple (InlineKeyboardMarkup с кнопками, название раздела)
    """
    if user_id is None:
        raise ValueError("user_id не должен быть None")
    logging.debug(f"Создание подменю. menu_key={menu_key}, user_id={user_id}")

    # Поиск данных для подменю по ключу
    data = next((v for k, v in LINKS.items() if v.get("key") == menu_key), None)
    section_name = next((k for k, v in LINKS.items()
                         if v.get("key") == menu_key), menu_key)
    if not data:
        logging.error(f"Раздел '{menu_key}' отсутствует в LINKS.")
        return InlineKeyboardMarkup(inline_keyboard=[]), section_name

    buttons = []
    subsections = data.get("subsections", {})
    for subsection, content in subsections.items():
        url = content.get("url")
        key = content.get("key")
        if url:
            buttons.append([InlineKeyboardButton(text=subsection, url=url)])
        elif key:
            callback_data = f"menu:{user_id}:{key}"
            buttons.append([InlineKeyboardButton(text=subsection,
                                                 callback_data=callback_data)])
        else:
            logging.warning(f"Пропущен подраздел '{subsection}' "
                            f"из-за некорректной структуры.")

    # Добавляем кнопку "Назад" для возврата в главное меню
    buttons.append([InlineKeyboardButton(text="⬅️ Назад",
                                         callback_data=f"menu:{user_id}:main")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard, section_name


def create_menu(menu_key: str = None, user_id: int = None):
    """
    Создаёт меню (главное или подменю) на основе LINKS.
    :param menu_key: Ключ раздела для подменю (None для главного меню)
    :param user_id: ID пользователя (для уникальных callback_data)
    :return: Tuple (InlineKeyboardMarkup с кнопками, название раздела)
    """
    logging.debug(f"Создание меню. menu_key={menu_key}, user_id={user_id}")
    if menu_key is None:
        return create_main_menu(user_id)
    else:
        return create_submenu(menu_key, user_id)
