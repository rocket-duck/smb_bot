import logging
from aiogram.filters import Command
from aiogram.types import Message
from bot.modules.commands_list import get_all_commands
from bot.database import SessionLocal
from bot.models import AdminUser

logger = logging.getLogger(__name__)


def is_user_admin_db(user_id: int) -> bool:
    """
    Проверяет, является ли пользователь администратором,
    запрашивая наличие активной записи в таблице admin_users.
    """
    session = SessionLocal()
    try:
        admin_record = session.query(AdminUser).filter(
            AdminUser.user_id == str(user_id),
            AdminUser.is_active.is_(True)
        ).first()
        return admin_record is not None
    except Exception as e:
        logger.error("Ошибка проверки админа в БД: %s", e)
        return False
    finally:
        session.close()


async def handle_help(message: Message):
    # Определяем, является ли пользователь администратором,
    # проверяя запись в БД.
    user_is_admin = is_user_admin_db(message.from_user.id)

    # Получаем полный список команд с учетом прав пользователя.
    commands = get_all_commands(user_is_admin=user_is_admin)
    logger.debug(f"Все команды: {commands}")

    # Определяем тип чата.
    chat_type = "private_chat" if message.chat.type == "private" \
        else "group_chat"

    # Фильтруем команды по типу чата и по видимости в справке.
    visible_commands = [
        cmd["command"] for cmd in commands
        if cmd.get(chat_type) and cmd.get("visible_in_help", True)
    ]
    logger.debug(f"Доступные команды для {chat_type} "
                 f"(admin={user_is_admin}): {visible_commands}")

    if not visible_commands:
        await message.answer("Нет доступных команд для вашего чата.")
        return

    # Формируем текст справки.
    help_text = "Привет! Вот список доступных команд:\n\n"
    for command in visible_commands:
        help_text += f"/{command.command} — {command.description}\n"

    await message.answer(help_text)


def register_help_handler(dp):
    """
    Регистрирует обработчик команды /help.
    :param dp: Экземпляр Dispatcher
    """
    dp.message.register(handle_help, Command(commands=["help"]))
