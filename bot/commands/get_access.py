import logging
from datetime import datetime
from typing import Tuple

from aiogram import Router, types
from aiogram.filters import Command
from bot.database import SessionLocal
from bot.models import AdminUser
from bot.config.flags import GET_ACCESS_ENABLE
from bot.config.tokens import ADMIN_USER_ID


logger = logging.getLogger(__name__)
router = Router()


async def access_already_granted(message: types.Message):
    session = SessionLocal()
    try:
        record = session.query(AdminUser).filter(
            AdminUser.user_id == str(message.from_user.id),
            AdminUser.is_active.is_(True)
        ).first()
        return record is not None
    except Exception as e:
        logger.error("Ошибка проверки доступа: %s", e)
        return False
    finally:
        session.close()


def prepare_admin_request(message: types.Message) \
        -> Tuple[str, types.InlineKeyboardMarkup]:
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username or ""
    request_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    admin_text = (
        f"Запрос на доступ!\n\n"
        f"User ID: {user_id}\n"
        f"Full Name: {full_name}\n"
        f"Username: @{username}\n"
        f"Время запроса: {request_time}"
    )
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Принять",
                                    callback_data=f"access:accept:{user_id}")],
        [types.InlineKeyboardButton(text="Отклонить",
                                    callback_data=f"access:decline:{user_id}")]
    ])
    return admin_text, keyboard


async def handle_get_access(message: types.Message) -> None:
    if message.chat.type != "private":
        await message.answer("Эта команда доступна только в "
                             "личных сообщениях с ботом.")
        return

    if not GET_ACCESS_ENABLE:
        await message.answer("Команда временно отключена.")
        return

    if await access_already_granted(message):
        await message.answer("Доступ уже предоставлен")
        return

    # Если доступа нет, отправляем запрос администратору
    await message.answer("Ожидайте предоставление доступа.")

    admin_text, keyboard = prepare_admin_request(message)
    try:
        # Замените "YOUR_ADMIN_CHAT_ID" на нужный ID
        # или используйте переменную из конфигурации
        await message.bot.send_message(chat_id=ADMIN_USER_ID,
                                       text=admin_text,
                                       reply_markup=keyboard)
    except Exception as e:
        logger.error("Ошибка отправки запроса администратору: %s", e)
        await message.answer("Произошла ошибка при отправке запроса "
                             "администратору. Попробуйте позже.")


async def handle_accept_callback(callback: types.CallbackQuery,
                                 user_id_str: str,
                                 target_user_id: int) \
        -> None:
    session = SessionLocal()
    try:
        admin_record = session.query(AdminUser).filter(
            AdminUser.user_id == user_id_str
        ).first()
        if not admin_record:
            admin_record = AdminUser(
                user_id=user_id_str,
                full_name=callback.from_user.full_name,
                username=callback.from_user.username or "",
                added_at=datetime.utcnow(),
                is_active=True
            )
            session.add(admin_record)
            session.commit()
        else:
            if not admin_record.is_active:
                admin_record.is_active = True
                admin_record.added_at = datetime.utcnow()
                session.commit()
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.bot.send_message(chat_id=target_user_id,
                                        text="Доступ предоставлен")
        await callback.answer("Доступ предоставлен.")
    except Exception as e:
        session.rollback()
        logger.error("Ошибка обработки accept callback: %s", e)
        await callback.answer("Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()


async def handle_decline_callback(callback: types.CallbackQuery,
                                  target_user_id: int) -> None:
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.bot.send_message(chat_id=target_user_id,
                                        text="Вам отказано в доступе")
        await callback.answer("Доступ отклонён.")
    except Exception as e:
        logger.error("Ошибка обработки decline callback: %s", e)
        await callback.answer("Произошла ошибка. Попробуйте позже.")


async def process_access_callback(callback: types.CallbackQuery) -> None:
    data_parts = callback.data.split(":")
    if len(data_parts) != 3:
        await callback.answer("Некорректные данные.")
        return

    _, action, user_id_str = data_parts
    try:
        target_user_id = int(user_id_str)
    except ValueError:
        await callback.answer("Некорректный user id.")
        return

    if action == "accept":
        await handle_accept_callback(callback, user_id_str, target_user_id)
    elif action == "decline":
        await handle_decline_callback(callback, target_user_id)
    else:
        await callback.answer("Неизвестное действие.")


def register_get_access_handler(dp) -> None:
    dp.message.register(handle_get_access,
                        Command(commands=["get_access"]))
    dp.callback_query.register(process_access_callback,
                               lambda cq: cq.data.startswith("access:"))
