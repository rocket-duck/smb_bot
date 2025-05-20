import logging
import re
import time

from collections import OrderedDict
from typing import Optional
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.services.search_service import ask_gpt


# Кэш для ответов поиска
class SearchCache:
    def __init__(self, max_size=100, ttl=3600):
        self.max_size = max_size
        self.ttl = ttl  # seconds
        self._cache = OrderedDict()
        self._ops = 0  # счетчик обращений

    def _cleanup(self):
        now = time.time()
        # Удаляем устаревшие записи
        to_delete = []
        for key, (answer, ts) in list(self._cache.items()):
            if now - ts > self.ttl:
                to_delete.append(key)
        for key in to_delete:
            del self._cache[key]

    def get(self, key):
        self._ops += 1
        if self._ops % 20 == 0:
            self._cleanup()
        item = self._cache.get(key)
        if item:
            answer, ts = item
            return answer
        return None

    def set(self, key, answer):
        self._ops += 1
        if self._ops % 20 == 0:
            self._cleanup()
        if key in self._cache:
            del self._cache[key]
        self._cache[key] = (answer, time.time())
        if len(self._cache) > self.max_size:
            self._cache.popitem(last=False)

search_cache = SearchCache(max_size=100, ttl=3600)

logger = logging.getLogger(__name__)
router = Router()


def sanitize_query(query: str) -> str:
    """
    Очищает пользовательский ввод от потенциально опасных символов.
    Удаляет управляющие символы и экранирует угловые скобки.
    Оставляет буквы, цифры, пробелы и базовую пунктуацию.
    Ограничивает длину результата 200 символами.
    """
    cleaned = re.sub(r'[<>]', '', query)
    cleaned = re.sub(r'[^\w\s\?\!\.,\-]', '', cleaned)  # убран \:
    result = cleaned.lstrip()
    return result[:200]  # limit length


async def cleanup_search_state(message, state):
    data = await state.get_data()
    msg_id = data.get("cancel_msg_id")
    if msg_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        except Exception:
            pass
    await state.clear()


@router.message.middleware()
async def catch_exceptions(handler, event, data):
    try:
        return await handler(event, data)
    except Exception as e:
        logger.exception("Unhandled error in search handler: %s", e)
        await event.answer("Внутренняя ошибка, попробуйте позже.")


# Определяем состояния для диалога поиска
class SearchState(StatesGroup):
    waiting_for_query = State()


@router.message(Command("search", prefix="/"))
async def cmd_search(message: types.Message, state: FSMContext) -> None:
    parts = message.text.split(maxsplit=1)
    additional_text: str = parts[1].strip() if len(parts) > 1 else ""

    if message.reply_to_message and message.reply_to_message.text:
        original = message.reply_to_message.text.strip()
        combined = f"{original} {additional_text}".strip()
        user_query = sanitize_query(combined)
        # Debounce: если такой запрос только что был, не повторяем
        data = await state.get_data()
        if data.get("last_query") == user_query:
            await message.answer("Вы уже отправляли этот запрос.")
            return
        await state.update_data(last_query=user_query)
        logger.info(
            "Команда /search вызвана в реплае пользователем %s, итоговый запрос: %s",
            message.from_user.id, user_query
        )
        await process_immediate_query(user_query, message, state)
        return

    if additional_text:
        user_query = sanitize_query(additional_text)
        data = await state.get_data()
        if data.get("last_query") == user_query:
            await message.answer("Вы уже отправляли этот запрос.")
            return
        await state.update_data(last_query=user_query)
        logger.info(
            "Команда /search вызвана с запросом от пользователя %s: %s",
            message.from_user.id, user_query
        )
        await process_immediate_query(user_query, message, state)
        return

    logger.info(
        "Команда /search вызвана без запроса, ожидается ввод пользователя %s",
        message.from_user.id
    )
    cancel_inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="cancel_search")]
        ]
    )
    sent = await message.answer(
        "Введите текст запроса для поиска или нажмите Отмена",
        reply_markup=cancel_inline_kb
    )
    await state.update_data(user_id=message.from_user.id, cancel_msg_id=sent.message_id)
    await state.set_state(SearchState.waiting_for_query)


async def process_immediate_query(user_query: str,
                                  message: types.Message,
                                  state: FSMContext) -> None:
    log_search_request_db(message, user_query)
    cache_key = (message.from_user.id, user_query)
    cached = search_cache.get(cache_key)
    if cached:
        logger.info("Используем кэшированный ответ для запроса: %s", user_query)
        answer = cached
    else:
        await message.answer("Обрабатываю ваш запрос...")
        try:
            answer: str = await ask_gpt(user_query)
        except Exception as e:
            logger.error("Ошибка в ask_gpt: %s", e)
            await message.answer("Ошибка при обработке запроса. Попробуйте позже.")
            await cleanup_search_state(message, state)
            return
        search_cache.set(cache_key, answer)
    await message.answer(answer)
    await cleanup_search_state(message, state)


async def is_command(message: types.Message) -> bool:
    """
    Фильтр, пропускающий только команды (тексты, начинающиеся с '/').
    """
    text = message.text or ""
    return text.strip().startswith("/")


@router.message(is_command, SearchState.waiting_for_query)
async def cancel_on_command(message: types.Message, state: FSMContext) -> None:
    logger.info("User %s initiated other command: cancel search", message.from_user.id)
    await cleanup_search_state(message, state)
    await message.answer("Операция отменена.")


@router.message(SearchState.waiting_for_query)
async def process_search_query(message: types.Message,
                               state: FSMContext) -> None:
    data = await state.get_data()
    invoking_user: Optional[int] = data.get("user_id")
    if message.from_user.id != invoking_user:
        logger.debug("Игнорирую сообщение от пользователя %s, "
                     "ожидался ввод от %s",
                     message.from_user.id, invoking_user)
        return

    if message.text.strip().lower() in ["отмена", "cancel"]:
        logger.info("Пользователь %s ввёл отмену", message.from_user.id)
        await cleanup_search_state(message, state)
        return

    raw_query = message.text.strip()
    user_query = sanitize_query(raw_query)

    # Debounce: если такой запрос уже был только что, не повторяем
    last_query = data.get("last_query")
    if last_query == user_query:
        logger.info("Повторный запрос от пользователя %s: %s", message.from_user.id, user_query)
        await message.answer("Вы уже отправляли этот запрос.")
        await cleanup_search_state(message, state)
        return

    logger.info("Пользователь %s ввёл запрос: %s",
                message.from_user.id, user_query)
    await state.update_data(last_query=user_query)
    await process_immediate_query(user_query, message, state)


def log_search_request_db(message: types.Message, user_query: str) -> None:
    """
    Логирует запрос пользователя в базу данных (таблица search_logs).
    """
    from bot.database import SessionLocal
    from bot.models import SearchLog
    session = SessionLocal()
    try:
        log_entry = SearchLog(
            user_id=str(message.from_user.id),
            username=message.from_user.username or "",
            full_name=message.from_user.full_name,
            query=user_query,
            timestamp=message.date  # или можно использовать datetime.utcnow()
        )
        session.add(log_entry)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error("Ошибка при записи лога запроса в базу данных: %s", e)
    finally:
        session.close()


def register(dp) -> None:
    """
    Регистрирует маршруты для команды /search в переданном Dispatcher.
    """
    dp.include_router(router)

@router.callback_query(lambda c: c.data == "cancel_search", SearchState.waiting_for_query)
async def cancel_search_callback(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    msg_id = data.get("cancel_msg_id")
    await state.clear()
    # Удаляем сообщение с инлайн-кнопкой "Отмена" (и текстом "Введите текст запроса для поиска:")
    if msg_id:
        try:
            await callback_query.bot.delete_message(
                chat_id=callback_query.message.chat.id,
                message_id=msg_id
            )
        except Exception:
            pass
