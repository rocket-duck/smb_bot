from aiogram.filters import Command
from aiogram.types import Message
from bot.modules.menu import create_menu
from bot.config.flags import DOCS_ENABLE
import logging
from aiogram.fsm.context import FSMContext

logger = logging.getLogger(__name__)

async def handle_docs(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает команду /docs.
    Сбрасывает активное FSM-состояние, проверяет идентификатор пользователя,
    затем, если DOCS_ENABLE включена, формирует меню для данного пользователя.
    Если меню пустое – информирует пользователя, иначе отправляет сообщение с меню.
    """
    # Сброс FSM-состояния
    await state.clear()

    # Получаем user_id, если он определён
    user_id = message.from_user.id if message.from_user and message.from_user.id else None
    if user_id is None:
        logger.error("Ошибка: невозможно определить идентификатор пользователя.")
        await message.answer("Ошибка: не удалось определить ваш идентификатор.")
        return

    logger.info(f"Команда /docs вызвана пользователем {user_id} (@{message.from_user.username}, {message.from_user.full_name})")

    if not DOCS_ENABLE:
        logger.warning("Команда /docs временно отключена.")
        await message.answer("Команда временно отключена.")
        return

    try:
        menu, _ = create_menu(user_id=user_id)
        if not menu.inline_keyboard:
            logger.warning("Главное меню пустое. Проверьте настройки LINKS.")
            await message.answer("Меню временно недоступно. Обратитесь к администратору.")
            return

        main_menu_text = "Вот какие ссылки я знаю.\nВыберите из меню ниже:"
        # Сохраняем текст главного меню в состоянии, если требуется для дальнейшей работы
        await state.update_data(main_menu_text=main_menu_text)

        await message.answer(main_menu_text, reply_markup=menu)
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /docs для пользователя {user_id}: {e}")
        await message.reply(f"Произошла ошибка: {e}")

def register_docs_handler(dp) -> None:
    """
    Регистрирует обработчик команды /docs.
    :param dp: Экземпляр Dispatcher.
    """
    dp.message.register(handle_docs, Command(commands=["docs"]))