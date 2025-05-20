import logging
from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot.config.links import LINKS

logger = logging.getLogger(__name__)

def create_menu(menu_key: str = None, user_id: int = None):
    """
    Создаёт меню (главное или подменю) на основе словаря LINKS.
    :param menu_key: Ключ раздела для подменю (None — главное меню)
    :param user_id: ID пользователя (для уникальных callback_data)
    :return: Tuple (InlineKeyboardMarkup, заголовок меню)
    """
    buttons = []
    if menu_key is None:
        # Главное меню
        for section, content in LINKS.items():
            url = content.get("url")
            key = content.get("key")
            if content.get("subsections"):
                cd = f"menu:{user_id}:{key}"
                buttons.append([InlineKeyboardButton(text=section, callback_data=cd)])
            elif url:
                # Листовой раздел в главном меню — прямая ссылка
                buttons.append([InlineKeyboardButton(text=section, url=url)])
        title = "Главное меню"
    else:
        # Подменю
        section_name = None
        for section, content in LINKS.items():
            if content.get("key") == menu_key:
                section_name = section
                for subsec, subcont in content.get("subsections", {}).items():
                    if subcont.get("subsections"):
                        # Вложенные подразделы
                        cd = f"menu:{user_id}:{subcont.get('key')}"
                        buttons.append([InlineKeyboardButton(text=subsec, callback_data=cd)])
                    elif subcont.get("url"):
                        # Листовой раздел в подменю — прямая ссылка
                        buttons.append([InlineKeyboardButton(text=subsec, url=subcont.get('url'))])
                break
        # Кнопка "Назад" в главное меню
        buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"menu:{user_id}:main")])
        title = section_name or "Меню"

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
