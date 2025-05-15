from typing import Tuple, Optional
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.modules.menu import create_menu
import logging

logger = logging.getLogger(__name__)


def parse_callback_data(data: str) -> Optional[Tuple[str, str, str]]:
    """
    Парсит callback_data, ожидая формат "menu:user_id:menu_key".
    Возвращает кортеж (prefix, user_id, menu_key),
    если данные корректны, иначе None.
    """
    parts = data.split(":")
    if len(parts) < 3:
        return None
    return parts[0], parts[1], parts[2]


async def handle_button(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обрабатывает нажатия на кнопки меню.

    Если callback_data соответствует формату "menu:user_id:menu_key", то:
      - Если menu_key == "main", открывает главное меню.
      - Иначе открывает подменю для указанного раздела.
    В случае ошибки или некорректных данных отправляет уведомление пользователю.
    """
    try:
        parsed = parse_callback_data(callback.data)
        if parsed is None:
            await callback.answer("Некорректные данные кнопки.")
            logger.error(f"Некорректные данные callback_data: {callback.data}")
            return

        prefix, user_id, menu_key = parsed

        if menu_key == "main":
            logger.debug(f"Открытие главного меню для user_id={user_id}")
            menu, _ = create_menu(user_id=user_id)
            # Получаем текст главного меню из состояния
            # или используем значение по умолчанию.
            user_data = await state.get_data()
            main_menu_text = user_data.get("main_menu_text", "Главное меню:")
            await callback.message.edit_text(
                main_menu_text,
                reply_markup=menu,
            )
        else:
            logger.debug(f"Открытие подменю '{menu_key}' для user_id={user_id}")
            menu, section_name = create_menu(menu_key=menu_key, user_id=user_id)
            if menu.inline_keyboard:
                await callback.message.edit_text(
                    f"Раздел: {section_name}:\nВыберите из меню ниже:",
                    reply_markup=menu,
                )
            else:
                await callback.answer("Этот раздел пуст.",
                                      show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка при обработке кнопки: {e}",
                     exc_info=True)
        await callback.answer("Произошла ошибка. Попробуйте снова.",
                              show_alert=True)


def register_button_handlers(dp) -> None:
    """
    Регистрирует обработчик callback_query для кнопок меню.
    Использует фильтр, чтобы обрабатывать только callback_data,
    начинающиеся с "menu:".
    """
    dp.callback_query.register(
        handle_button,
        lambda callback: callback.data.startswith("menu:")
    )
