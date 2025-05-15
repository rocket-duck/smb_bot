import asyncio
import logging
import openai
from typing import Optional

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from bot.config.tokens import OPENAI_API_KEY
from bot.config.gpt_prompt import PROMPT

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

openai.api_key = OPENAI_API_KEY
router = Router()


# Определяем состояния для диалога поиска
class SearchState(StatesGroup):
    waiting_for_query = State()


@router.message(Command("search", prefix="/"))
async def cmd_search(message: types.Message, state: FSMContext) -> None:
    """
    Обрабатывает команду /search.
    Если команда вызвана с дополнительным текстом
    или в реплае – обрабатывается немедленно.
    Иначе переводит пользователя в режим ожидания ввода,
    сохраняя ID вызывающего.
    """
    parts = message.text.split(maxsplit=1)
    additional_text: str = parts[1].strip() if len(parts) > 1 else ""
    reply_text: str = ""
    if message.reply_to_message and message.reply_to_message.text:
        reply_text = message.reply_to_message.text.strip()

    # Формирование итогового запроса на основе реплая и дополнительного текста
    if reply_text:
        user_query: str = reply_text + (f" {additional_text}"
                                        if additional_text else "")
        logging.info("Команда /search вызвана в реплае "
                     "пользователем %s, итоговый запрос: %s",
                     message.from_user.id, user_query)
        await process_immediate_query(user_query, message, state)
        return
    elif additional_text:
        user_query = additional_text
        logging.info("Команда /search вызвана с запросом "
                     "от пользователя %s: %s",
                     message.from_user.id, user_query)
        await process_immediate_query(user_query, message, state)
        return
    else:
        # Если дополнительных данных нет – переводим в режим ожидания ввода
        logging.info("Команда /search вызвана без запроса, "
                     "ожидается ввод пользователя %s",
                     message.from_user.id)
        await message.answer("Введите текст запроса для "
                             "поиска (или напишите «отмена»):")
        await state.update_data(user_id=message.from_user.id)
        await state.set_state(SearchState.waiting_for_query)
        asyncio.create_task(search_timeout(message, state))


async def process_immediate_query(user_query: str,
                                  message: types.Message,
                                  state: FSMContext) -> None:
    """
    Обрабатывает запрос, который можно выполнить сразу.
    Записывает запрос в базу, отправляет сообщение "Обрабатываю ваш запрос...",
    вызывает ChatGPT и отправляет результат в чат.
    """
    log_search_request_db(message, user_query)
    await message.answer("Обрабатываю ваш запрос...")
    answer: str = await query_openai(user_query, message)
    await message.answer(answer)
    await state.clear()


async def search_timeout(message: types.Message, state: FSMContext) -> None:
    """
    Если в течение 120 секунд не поступил запрос – отменяет режим ожидания.
    """
    await asyncio.sleep(120)
    current_state: Optional[str] = await state.get_state()
    if current_state == SearchState.waiting_for_query.state:
        logging.info("Таймаут: пользователь %s не ввёл запрос за 120 секунд",
                     message.from_user.id)
        await message.answer("Код ошибки R0604.\n"
                             "Время ожидания истекло, операция отменена.")
        await state.clear()


@router.message(lambda m: m.text and m.text.strip().startswith("/"),
                SearchState.waiting_for_query)
async def cancel_on_command(message: types.Message, state: FSMContext) -> None:
    """
    Если в режиме ожидания пользователь вызывает
    другую команду – отменяет ожидание.
    """
    logging.info("Пользователь %s вызвал другую команду, "
                 "завершаем ожидание поиска",
                 message.from_user.id)
    await state.clear()


@router.message(SearchState.waiting_for_query)
async def process_search_query(message: types.Message,
                               state: FSMContext) -> None:
    """
    Обрабатывает ввод в режиме ожидания.
    Проверяет, что сообщение пришло от того же
    пользователя, который вызвал команду.
    При вводе "отмена" или "cancel" – отменяет операцию.
    Иначе обрабатывает запрос.
    """
    data = await state.get_data()
    invoking_user: Optional[int] = data.get("user_id")
    if message.from_user.id != invoking_user:
        logging.debug("Игнорирую сообщение от пользователя %s, "
                      "ожидался ввод от %s",
                      message.from_user.id, invoking_user)
        return

    if message.text.strip().lower() in ["отмена", "cancel"]:
        logging.info("Пользователь %s ввёл отмену", message.from_user.id)
        await message.answer("Операция отменена.")
        await state.clear()
        return

    user_query = message.text.strip()
    logging.info("Пользователь %s ввёл запрос: %s",
                 message.from_user.id, user_query)
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
        logging.error("Ошибка при записи лога запроса в базу данных: %s", e)
    finally:
        session.close()


async def query_openai(user_query: str, message: types.Message) -> str:
    """
    Отправляет запрос в OpenAI и возвращает ответ.
    """
    try:
        logging.info("Отправка запроса в OpenAI для пользователя %s",
                     message.from_user.id)
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": PROMPT},
                    {"role": "user", "content": user_query}
                ],
                max_tokens=500,
                temperature=0.7
            )
        )
        answer: str = response.choices[0].message.content.strip()
        logging.info("Получен ответ от OpenAI для пользователя %s: %s",
                     message.from_user.id, answer)
        return answer
    except Exception as e:
        logging.error("Ошибка вызова OpenAI API для пользователя %s: %s",
                      message.from_user.id, e)
        return "Произошла ошибка при обработке запроса. Попробуйте позже."


def register_search_handler(dp) -> None:
    dp.include_router(router)
