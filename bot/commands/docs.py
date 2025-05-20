from aiogram.types import Message, InlineKeyboardMarkup
import logging
import functools
from typing import Callable, Awaitable, Tuple
from aiogram.fsm.context import FSMContext
from bot.services.docs_service import get_docs_menu, DocsServiceDisabled, EmptyDocsMenu
from aiogram import Router, Dispatcher
from aiogram.filters import Command
from bot.config.flags import DOCS_ENABLE

logger = logging.getLogger(__name__)

@functools.lru_cache(maxsize=128)
def build_docs_response(user_id: int) -> Tuple[InlineKeyboardMarkup, str]:
    """
    Возвращает (menu, text) для пользователя, с кешированием.
    """
    return get_docs_menu(user_id)

router = Router()

@router.message.middleware()
async def docs_enabled_checker(handler, event, data):
    """
    Блокирует команду, если DOCS_ENABLE = False.
    """
    if not DOCS_ENABLE:
        await event.answer("Команда временно отключена.")
        return
    return await handler(event, data)

def catch_docs_errors(fn: Callable[[Message, FSMContext], Awaitable[None]]) -> Callable[[Message, FSMContext], Awaitable[None]]:
    """
    Декоратор для перехвата и обработки ошибок в handle_docs.
    """
    @functools.wraps(fn)
    async def wrapper(message: Message, state: FSMContext) -> None:
        try:
            await fn(message, state)
        except DocsServiceDisabled:
            await message.answer("Команда временно отключена.")
        except EmptyDocsMenu:
            await message.answer("Меню временно недоступно. Обратитесь к администратору.")
        except Exception as e:
            logger.exception(f"Error in handle_docs: {e}")
            await message.reply("Произошла внутренняя ошибка. Попробуйте позже.")
    return wrapper

@catch_docs_errors
async def handle_docs(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает команду /docs.
    Сбрасывает активное FSM-состояние, проверяет идентификатор пользователя,
    затем, если DOCS_ENABLE включена, формирует меню для данного пользователя.
    Если меню пустое – информирует пользователя, иначе отправляет сообщение с меню.

    :param message: Входящее сообщение с командой /docs
    :param state: FSMContext для управления состоянием
    :return: None
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

    # Формируем меню и текст
    menu, main_menu_text = build_docs_response(user_id)
    # Сохраняем текст главного меню в состоянии
    await state.update_data(main_menu_text=main_menu_text)
    # Логируем количество разделов
    sections = len(menu.inline_keyboard) if hasattr(menu, "inline_keyboard") else 0
    logger.debug(f"Docs menu for user {user_id} has {sections} sections")
    await message.answer(main_menu_text, reply_markup=menu)

# Router setup for /docs command
router.message.register(handle_docs, Command(commands=["docs"]))

def register(dp: Dispatcher) -> None:
    """
    Регистрирует обработчик /docs через Router.
    """
    dp.include_router(router)
