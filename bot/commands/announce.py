import logging
from typing import Optional, Tuple, Dict, Any

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from bot.config.flags import ANNOUNCE_ENABLE
from bot.database import SessionLocal
from bot.models import Chat, AdminUser

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
    session = SessionLocal()
    try:
        chat_list_db = session.query(Chat).filter(Chat.deleted.is_(False)).all()
    except Exception as e:
        logger.error("Ошибка получения списка чатов: %s", e)
        chat_list_db = []
    finally:
        session.close()

    if not chat_list_db:
        await message.answer("Нет активных чатов для отправки.")
        return

    chat_list = [{"id": chat.chat_id,
                  "title": chat.title} for chat in chat_list_db]
    for chat in chat_list:
        await send_announce_to_chat(chat,
                                    message,
                                    announce_message,
                                    reply_to_message)

    await message.answer("Сообщение отправлено во все активные чаты.")


@router.message(Command("announce", prefix="/"))
async def handle_announce(message: types.Message, state: FSMContext) -> None:
    # Проверка прав: доступ только для администраторов
    session = SessionLocal()
    try:
        admin_record = session.query(AdminUser).filter(
            AdminUser.user_id == str(message.from_user.id),
            AdminUser.is_active.is_(True)
        ).first()
    except Exception as e:
        logger.error("Ошибка проверки прав администратора: %s", e)
        admin_record = None
    finally:
        session.close()

    if not admin_record:
        await message.answer("У вас нет прав для использования команды.\n"
                             "Запросить права вы можете командой /get_access")
        return

    if not ANNOUNCE_ENABLE:
        await message.answer("Команда временно отключена.")
        return

    announce_text, reply_msg = await prepare_announce(message)
    if announce_text is None and reply_msg is None:
        await message.answer("Введите текст для рассылки "
                             "в чаты или введите \"отмена\":")
        await state.set_state(AnnounceState.waiting_for_announce)
        await state.update_data(initial_reply_id=message.message_id)
        return

    await process_announce(message, announce_text, reply_msg)


@router.message(AnnounceState.waiting_for_announce)
async def process_announce_input(message: types.Message,
                                 state: FSMContext) -> None:
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


def register_announce_handler(dp) -> None:
    dp.message.register(handle_announce,
                        Command(commands=["announce"]))
    dp.message.register(process_announce_input,
                        AnnounceState.waiting_for_announce)
