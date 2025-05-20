import re

from typing import Optional
from aiogram.types import Message, MessageEntity
from aiogram.fsm.context import FSMContext

from bot.config.flags import KEYWORD_RESPONSES_ENABLE

def sanitize_text(text: str) -> str:
    """
    Очищает входной текст от нежелательных символов и ограничивает длину до 200 символов.
    Удаляет всё, кроме букв, цифр, пробелов и базовой пунктуации (?!.,-).
    """
    cleaned = re.sub(r'[^\w\s\?\!\.\,\-]', '', text)
    return cleaned[:200]

def should_process_text(text: str) -> bool:
    """
    Определяет, нужно ли обрабатывать текст:
    - глобальный флаг KEYWORD_RESPONSES_ENABLE должен быть включён
    - текст не пустой и не начинается с '/'
    """
    if not KEYWORD_RESPONSES_ENABLE:
        return False
    stripped = text.strip()
    if not stripped or stripped.startswith('/'):
        return False
    return True

async def no_fsm_filter(message: Message, state: FSMContext) -> bool:
    """
    Фильтр, который пропускает сообщения в handler только если:
    - либо нет сохранённого user_id в state (нет активного ожидания)
    - либо сообщение пришло от пользователя, который инициировал ожидание
    """
    data = await state.get_data()
    invoking_user: Optional[int] = data.get("user_id")
    if invoking_user is None:
        return True
    return message.from_user.id == invoking_user

async def skip_empty(message: Message, state: FSMContext) -> bool:
    """
    Пропускает сообщения только если они не пустые.
    """
    text = message.text or ""
    return bool(text.strip())

async def skip_slash_command(message: Message) -> bool:
    """
    Пропускает сообщения, не являющиеся бот-командами.
    Отклоняет любые сообщения, начинающиеся с '/' или содержащие entity type 'bot_command' at offset 0.
    """
    entities = message.entities or []
    for ent in entities:
        if ent.type == "bot_command" and ent.offset == 0:
            return False
    return True
