from aiogram.types import CallbackQuery
from bot.menu.main_menu import create_main_menu
from bot.menu.submenu import create_submenu

async def handle_button(callback: CallbackQuery):
    """
    Обрабатывает нажатия на кнопки.

    :param callback: CallbackQuery от пользователя
    """
    menu_key = callback.data.split(":")[1]

    if menu_key == "main":
        await callback.message.edit_text("Главное меню:", reply_markup=create_main_menu())
    else:
        await callback.message.edit_text(f"Раздел: {menu_key.capitalize()}:", reply_markup=create_submenu(menu_key))

def register_button_handlers(dp):
    """
    Регистрирует обработчик нажатий на кнопки.

    :param dp: Экземпляр Dispatcher
    """
    dp.callback_query.register(handle_button, lambda callback: callback.data.startswith("menu:"))