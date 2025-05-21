import logging
from typing import Dict
from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot.config.links import LINKS

logger = logging.getLogger(__name__)

def create_menu(menu_key: str = None, user_id: int = None):
    """
    Создаёт меню: главное (категории) или подменю (ссылки в категории) на основе списка LINKS.
    :param menu_key: Название категории для подменю (None — главное меню)
    :param user_id: ID пользователя (для уникальных callback_data)
    :return: Tuple (InlineKeyboardMarkup, заголовок меню)
    """
    # Build mapping from category slug to display name
    category_map: Dict[str, str] = {}
    for entry in LINKS:
        slug = entry["id"].split(".", 1)[0]
        path = entry.get("path") or []
        # Only map entries with a non-empty path
        if path and slug not in category_map:
            category_map[slug] = path[0]

    buttons = []
    if menu_key is None or menu_key == "main":
        # Главное меню: список категорий
        for slug, display in sorted(category_map.items(), key=lambda kv: kv[1]):
            cd = f"menu:{user_id}:{slug}"
            buttons.append([InlineKeyboardButton(text=display, callback_data=cd)])
        title = "Главное меню"

        # Добавить прямые ссылки для разделов без категории (empty or missing path)
        for entry in LINKS:
            if not entry.get("path"):
                buttons.append([InlineKeyboardButton(text=entry["name"], url=entry["url"])])

    else:
        # Подменю для выбранной категории slug==menu_key
        display_name = category_map.get(menu_key, menu_key)
        for entry in LINKS:
            if entry["id"].split(".", 1)[0] == menu_key:
                buttons.append([InlineKeyboardButton(text=entry["name"], url=entry["url"])])
        # Кнопка "Назад"
        buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"menu:{user_id}:main")])
        title = display_name

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard, title


# --- Handler and registration for menu navigation and link sending ---
async def handle_menu(callback: types.CallbackQuery):
    """
    Обработчик callback_query для навигации по меню документации и отправки ссылок.
    """
    data = callback.data or ""

    # Навигация по меню
    if not data.startswith("menu:"):
        return
    try:
        _, uid_str, menu_key = data.split(":", 2)
        uid = int(uid_str)
    except ValueError:
        logger.error(f"Incorrect menu callback_data format: {data}")
        await callback.answer("Ошибка навигации. Попробуйте снова.", show_alert=True)
        return

    key = None if menu_key == "main" else menu_key
    keyboard, title = create_menu(key, uid)
    await callback.message.edit_text(title, reply_markup=keyboard)
    await callback.answer()


def register(dp: Dispatcher):
    """
    Регистрирует обработчик callback для menu:
    """
    dp.callback_query.register(
        handle_menu,
        lambda c: c.data and c.data.startswith("menu:")
    )
