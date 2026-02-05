import logging
from typing import Any, Dict, Optional, Tuple

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from bot.config.flags import ANNOUNCE_ENABLE
from bot.database import SessionLocal
from bot.models import Chat
from bot.utils.command_registry import command

logger = logging.getLogger(__name__)
router = Router()


class AnnounceState(StatesGroup):
    """Состояния FSM для команды announce."""
    waiting_for_announce = State()


async def prepare_announce(message: types.Message) -> Tuple[Optional[str], Optional[types.Message]]:
    if message.reply_to_message:
        if message.text.startswith("/announce"):
            additional_text = message.text.replace("/announce", "", 1).strip()
        else:
            additional_text = message.text.strip()
        return additional_text if additional_text else None, message.reply_to_message
    else:
        if message.text.startswith("/announce"):
            parts = message.text.split(maxsplit=1)
            additional_text: str = parts[1].strip() if len(parts) > 1 else ""
        else:
            additional_text = message.text.strip()
        return additional_text if additional_text else None, None


async def send_announce_to_chat(
    chat: Dict[str, Any],
    message: types.Message,
    announce_message: Optional[str],
    reply_to_message: Optional[types.Message],
) -> None:
    """Отправляет рассылку в один чат."""
    try:
        if announce_message:
            await message.bot.send_message(chat["id"], announce_message)
        if reply_to_message:
            await reply_to_message.forward(chat["id"])
    except Exception as e:
        logger.warning(
            "Не удалось отправить сообщение в чат %s (%s): %s",
            chat["id"],
            chat["title"],
            e,
        )


async def process_announce(
    message: types.Message,
    announce_message: Optional[str],
    reply_to_message: Optional[types.Message],
) -> None:
    async with SessionLocal() as session:
        try:
            result = await session.execute(
                select(Chat).filter(Chat.deleted.is_(False))
            )
            chat_list_db = result.scalars().all()
        except Exception as e:
            logger.error("Ошибка получения списка чатов: %s", e)
            chat_list_db = []

    if not chat_list_db:
        await message.answer("Нет активных чатов для отправки.")
        return

    chat_list = [{"id": chat.chat_id, "title": chat.title} for chat in chat_list_db]
    for chat in chat_list:
        await send_announce_to_chat(
            chat,
            message,
            announce_message,
            reply_to_message,
        )

    await message.answer("Сообщение отправлено во все активные чаты.")


@command("announce", flag=ANNOUNCE_ENABLE, router=router)
async def handle_announce(message: types.Message, state: FSMContext) -> None:
    announce_text, reply_msg = await prepare_announce(message)
    if announce_text is None and reply_msg is None:
        await message.answer(
            "Введите текст для рассылки в чаты или введите \"отмена\":"
        )
        await state.set_state(AnnounceState.waiting_for_announce)
        await state.update_data(initial_reply_id=message.message_id)
        return

    await process_announce(message, announce_text, reply_msg)


@router.message(AnnounceState.waiting_for_announce)
async def process_announce_input(message: types.Message, state: FSMContext) -> None:
    if message.text.strip().lower() in ["отмена", "cancel"]:
        await message.answer("Рассылка отменена.")
        await state.clear()
        return

    announce_text, reply_msg = await prepare_announce(message)
    if announce_text is None and reply_msg is None:
        await message.answer("Неверный ввод. Попробуйте снова.")
        return

    await process_announce(message, announce_text, reply_msg)
    await state.clear()
