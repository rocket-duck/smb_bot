import asyncio
import logging

import openai
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from openai import BadRequestError, OpenAIError, RateLimitError
from sqlalchemy import insert
from sqlalchemy.exc import SQLAlchemyError

from bot.config.flags import SEARCH_ENABLE, SEARCH_MAX_QUERY_LEN, SEARCH_TIMEOUT_SECONDS
from bot.config.gpt_prompt import PROMPT
from bot.config.settings import get_settings
from bot.database import SessionLocal
from bot.utils.command_registry import command

settings = get_settings()
openai.api_key = settings.openai_api_key
router = Router()

_timeout_tasks: set[asyncio.Task] = set()


class SearchState(StatesGroup):
    """Состояния для диалога поиска."""

    waiting_for_query = State()


def _track_timeout_task(task: asyncio.Task) -> None:
    _timeout_tasks.add(task)
    task.add_done_callback(_timeout_tasks.discard)
    task.add_done_callback(
        lambda t: logging.error("search_timeout завершился с ошибкой: %s", t.exception())
        if not t.cancelled() and t.exception()
        else None
    )


@command("search", flag=SEARCH_ENABLE, router=router)
async def cmd_search(message: types.Message, state: FSMContext) -> None:
    """Обрабатывает команду /search."""
    parts = message.text.split(maxsplit=1)
    additional_text: str = parts[1].strip() if len(parts) > 1 else ""
    reply_text: str = ""
    if message.reply_to_message and message.reply_to_message.text:
        reply_text = message.reply_to_message.text.strip()

    if reply_text:
        user_query: str = reply_text + (
            f" {additional_text}" if additional_text else ""
        )
        logging.info("Команда /search вызвана в реплае.")
        await process_immediate_query(user_query, message, state)
        return
    elif additional_text:
        user_query = additional_text
        logging.info("Команда /search вызвана с запросом.")
        await process_immediate_query(user_query, message, state)
        return
    else:
        logging.info("Команда /search вызвана без запроса, ожидается ввод.")
        await message.answer(
            "Введите текст запроса для поиска (или напишите «отмена»):"
        )
        await state.update_data(user_id=message.from_user.id)
        await state.set_state(SearchState.waiting_for_query)
        _track_timeout_task(asyncio.create_task(search_timeout(message, state)))


async def process_immediate_query(
    user_query: str, message: types.Message, state: FSMContext
) -> None:
    """Обрабатывает запрос, который можно выполнить сразу."""
    if len(user_query) > SEARCH_MAX_QUERY_LEN:
        await message.answer(
            f"Запрос слишком длинный (максимум {SEARCH_MAX_QUERY_LEN} символов)."
        )
        await state.clear()
        return
    await log_search_request_db(message, user_query)
    await message.answer("Обрабатываю ваш запрос...")
    answer: str = await query_openai(user_query, message)
    await message.answer(answer)
    await state.clear()


async def search_timeout(message: types.Message, state: FSMContext) -> None:
    """Отменяет режим ожидания, если не поступил запрос."""
    await asyncio.sleep(SEARCH_TIMEOUT_SECONDS)
    current_state: str | None = await state.get_state()
    if current_state == SearchState.waiting_for_query.state:
        logging.info(
            "Таймаут ожидания запроса /search (%d секунд).", SEARCH_TIMEOUT_SECONDS
        )
        await message.answer(
            "Код ошибки R0604.\nВремя ожидания истекло, операция отменена."
        )
        await state.clear()


@router.message(
    lambda m: m.text and m.text.strip().startswith("/"), SearchState.waiting_for_query
)
async def cancel_on_command(message: types.Message, state: FSMContext) -> None:
    """Если во время ожидания пользователь вызывает другую команду."""
    logging.info("Пользователь вызвал другую команду, ожидание поиска завершено.")
    await state.clear()


@router.message(SearchState.waiting_for_query)
async def process_search_query(message: types.Message, state: FSMContext) -> None:
    """Обрабатывает ввод в режиме ожидания."""
    data = await state.get_data()
    invoking_user: int | None = data.get("user_id")
    if message.from_user.id != invoking_user:
        logging.debug("Игнорирую сообщение: ожидался ввод от другого пользователя.")
        return

    if message.text.strip().lower() in ["отмена", "cancel"]:
        logging.info("Пользователь отменил запрос /search.")
        await message.answer("Операция отменена.")
        await state.clear()
        return

    user_query = message.text.strip()
    logging.info("Получен запрос от пользователя.")
    await process_immediate_query(user_query, message, state)


async def log_search_request_db(message: types.Message, user_query: str) -> None:
    """Логирует запрос пользователя в базу данных (таблица search_logs)."""
    from bot.models import SearchLog

    async with SessionLocal() as session:
        try:
            stmt = insert(SearchLog).values(
                user_id=message.from_user.id,
                username=message.from_user.username or "",
                full_name=message.from_user.full_name,
                query=user_query,
                timestamp=message.date,
            )
            await session.execute(stmt)
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            logging.error("Ошибка при записи лога запроса в базу данных: %s", e)


async def query_openai(user_query: str, message: types.Message) -> str:
    """Отправляет запрос в OpenAI и возвращает ответ."""
    try:
        logging.debug("Отправка запроса в OpenAI.")
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": PROMPT},
                    {"role": "user", "content": user_query},
                ],
                max_tokens=500,
                temperature=0.7,
            ),
        )
        answer: str = response.choices[0].message.content.strip()
        logging.debug("Получен ответ от OpenAI.")
        return answer
    except RateLimitError as e:
        logging.error("Rate limit error from OpenAI: %s", e)
        return "Превышена квота OpenAI. Попробуйте позже."
    except BadRequestError as e:
        logging.error("Invalid request error from OpenAI: %s", e)
        return "Некорректный запрос к OpenAI. Обратитесь в поддержку."
    except OpenAIError as e:
        logging.error("Ошибка вызова OpenAI API: %s", e)
        return "Произошла ошибка при обработке запроса. Попробуйте позже."
