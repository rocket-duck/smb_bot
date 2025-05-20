import logging
import asyncio

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from typing import Optional, Tuple, Dict, Any
from html import escape
from aiogram import Router, types, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from bot.config.flags import ANNOUNCE_ENABLE
from bot.services.admin_service import is_user_admin
from bot.services.announce_service import get_active_chats


logger = logging.getLogger(__name__)
router = Router()


# Определяем FSM для команды announce
class AnnounceState(StatesGroup):
    waiting_for_announce = State()


async def prepare_announce(message: types.Message) -> (
        Tuple)[Optional[str], Optional[types.Message]]:
    if message.reply_to_message:
        if message.text.startswith("/announce"):
            additional_text = message.text.replace("/announce", "", 1).strip()
        else:
            additional_text = message.text.strip()
        return (additional_text if additional_text else None,
                message.reply_to_message)
    else:
        if message.text.startswith("/announce"):
            parts = message.text.split(maxsplit=1)
            additional_text: str = parts[1].strip() if len(parts) > 1 else ""
        else:
            additional_text = message.text.strip()
        return additional_text if additional_text else None, None


async def send_announce_to_chat(chat: Dict[str, Any],
                                message: types.Message,
                                announce_message: Optional[str],
                                reply_to_message: Optional[types.Message])\
        -> None:
    """
    Отправляет рассылку в один чат: если announce_message задан, отправляет его,
    если reply_to_message задан, пересылает его.
    """
    try:
        if announce_message:
            await message.bot.send_message(chat["id"], announce_message)
        if reply_to_message:
            await reply_to_message.forward(chat["id"])
    except Exception as e:
        logger.warning(f"Не удалось отправить сообщение в чат "
                       f"{chat['id']} ({chat['title']}): {e}")


async def process_announce(message: types.Message,
                           announce_message: Optional[str],
                           reply_to_message: Optional[types.Message]) -> None:
    """
    Рассылает сообщение или пересылку во все активные чаты параллельно.
    """
    chat_list = get_active_chats()
    if not chat_list:
        await message.answer("Нет активных чатов для отправки.")
        return

    # Параллельная рассылка
    loop = asyncio.get_running_loop()
    tasks = [
        loop.create_task(
            send_announce_to_chat(chat, message, announce_message, reply_to_message)
        )
        for chat in chat_list
    ]
    await asyncio.gather(*tasks, return_exceptions=True)
    await message.answer("Сообщение отправлено во все активные чаты.")


@router.message(Command("announce", prefix="/"))
async def handle_announce(message: types.Message, state: FSMContext) -> None:
    """
    Обрабатывает команду /announce: проверяет права, собирает текст или пересылку,
    и запускает рассылку.
    """
    # Проверка прав через сервис
    loop = asyncio.get_running_loop()
    try:
        is_admin = await loop.run_in_executor(None, is_user_admin, message.from_user.id)
    except Exception as e:
        logger.error(f"Ошибка проверки прав администратора: {e}")
        await message.answer("Произошла ошибка при проверке прав администратора.")
        return
    if not is_admin:
        await message.answer(
            "У вас нет прав для использования команды.\n"
            "Запросить права вы можете командой /get_access"
        )
        return

    if not ANNOUNCE_ENABLE:
        await message.answer("Команда временно отключена.")
        return

    # Подготовка и валидация ввода
    announce_text, reply_msg = await prepare_announce(message)
    # Санитизация текста
    if announce_text:
        announce_text = escape(announce_text)
    if announce_text is None and reply_msg is None:
        # === ДОБАВЛЯЕМ INLINE КНОПКУ "ОТМЕНА" ===
        cancel_inline_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Отмена", callback_data="cancel_announce")]
            ]
        )
        sent = await message.answer(
            "Введите текст для рассылки в чаты или нажмите «Отмена»:",
            reply_markup=cancel_inline_kb
        )
        await state.set_state(AnnounceState.waiting_for_announce)
        await state.update_data(initial_reply_id=message.message_id, cancel_msg_id=sent.message_id)
        return

    await process_announce(message, announce_text, reply_msg)


@router.message(AnnounceState.waiting_for_announce)
async def process_announce_input(message: types.Message,
                                 state: FSMContext) -> None:
    """
    Получает текст для рассылки из состояния FSM, санитизирует и отправляет.
    """
    data = await state.get_data()
    cancel_msg_id = data.get("cancel_msg_id")
    if cancel_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, cancel_msg_id)
        except Exception:
            pass

    if message.text.strip().lower() in ["отмена", "cancel"]:
        await state.clear()
        return

    announce_text, reply_msg = await prepare_announce(message)
    # Санитизация текста
    if announce_text:
        announce_text = escape(announce_text)
    if announce_text is None and reply_msg is None:
        await message.answer("Неверный ввод. Попробуйте снова.")
        return

    await process_announce(message, announce_text, reply_msg)
    await state.clear()


def register(dp: Dispatcher) -> None:
    """
    Register announce command handlers by including the router.
    """
    dp.include_router(router)


# === CALLBACK HANDLER ДЛЯ КНОПКИ ОТМЕНЫ ===
@router.callback_query(lambda c: c.data == "cancel_announce", AnnounceState.waiting_for_announce)
async def cancel_announce_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cancel_msg_id = data.get("cancel_msg_id")
    if cancel_msg_id:
        try:
            await callback.bot.delete_message(callback.message.chat.id, cancel_msg_id)
        except Exception:
            pass
    await callback.answer()
    await state.clear()