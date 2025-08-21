import logging
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.config.flags import DOCS_ENABLE
from bot.modules.menu import create_menu
from bot.utils.command_registry import command

logger = logging.getLogger(__name__)


@command("docs", flag=DOCS_ENABLE)
async def handle_docs(message: Message, state: FSMContext) -> None:
    """Обрабатывает команду /docs."""
    await state.clear()
    user_id = message.from_user.id if message.from_user and message.from_user.id else None
    if user_id is None:
        logger.error("Ошибка: невозможно определить идентификатор пользователя.")
        await message.answer("Ошибка: не удалось определить ваш идентификатор.")
        return

    logger.info(
        "Команда /docs вызвана пользователем %s (@%s, %s)",
        user_id,
        message.from_user.username,
        message.from_user.full_name,
    )

    try:
        menu, _ = create_menu(user_id=user_id)
        if not menu.inline_keyboard:
            logger.warning("Главное меню пустое. Проверьте настройки LINKS.")
            await message.answer("Меню временно недоступно. Обратитесь к администратору.")
            return

        main_menu_text = "Вот какие ссылки я знаю.\nВыберите из меню ниже:"
        await state.update_data(main_menu_text=main_menu_text)
        await message.answer(main_menu_text, reply_markup=menu)
    except Exception as e:
        logger.error(
            "Ошибка при обработке команды /docs для пользователя %s: %s",
            user_id,
            e,
        )
        await message.reply(f"Произошла ошибка: {e}")
