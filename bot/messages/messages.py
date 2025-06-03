import asyncio
import logging
from datetime import datetime, timedelta
import random

from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from bot.messages.message_parse import find_links_by_keyword
from bot.messages.who_request import handle_who_request
from bot.messages.bot_tag import handle_bot_tag
from bot.utils.participants import update_participant
from bot.messages.maslina import handle_maslina   # импортируем новый модуль
from bot.config.tokens import BOT_USERNAME
from bot.config.flags import (
    KEYWORD_RESPONSES_ENABLE,
    TIMEOUT_RESPONSES_ENABLE,
    WHO_REQUEST_ENABLE,
    BOT_TAG_ENABLE,
    MASLINA_ENABLE
)

# Настройка времени таймаута (в минутах)
TIMEOUT_MINUTES: int = 60

# Хранилище для предотвращения повторных ответов (по чатам)
recent_links: dict = {}  # Формат: {chat_id: {"url": время последнего ответа}}

# Хранилище для подсчета лайков и дизлайков: {(chat_id, message_id): {"likes": int, "dislikes": int}}
reaction_counts: dict = {}


def should_process_text(text: str) -> bool:
    """
    Возвращает True, если текст сообщения должен быть обработан.
    Проверяются:
      - Если текст ровно равен упоминанию бота
      - Если сообщение начинается со слеша (команда)
      - Если функция парсинга сообщений отключена
    """
    if should_ignore_bot_mention(text, BOT_USERNAME):
        logging.debug("Сообщение равно упоминанию бота, обработка прекращена.")
        return False
    if text.startswith("/"):
        logging.debug(f"Сообщение {text} игнорируется, так как это команда.")
        return False
    if not KEYWORD_RESPONSES_ENABLE:
        logging.debug("Функция парсинга сообщений отключена")
        return False
    return True


def should_ignore_bot_mention(text: str, bot_username) -> bool:
    """
    Возвращает True, если текст сообщения ровно равен упоминанию бота.
    """
    normalized_username = bot_username[0] \
        if isinstance(bot_username, tuple) \
        else bot_username
    return text.lower() == f"@{normalized_username.lower()}"


async def handle_message(message: Message, state: FSMContext) -> None:
    """
    Основная функция для обработки текстовых сообщений пользователя.
    """
    if not message.text:
        logging.debug("Сообщение не содержит текста, обработка пропущена.")
        return

    text: str = message.text.strip()

    # Обновляем или добавляем участника в БД на основе сообщения
    update_participant(message)

    # Обработка дополнительных фановых триггеров
    await handle_bot_tag(message, BOT_USERNAME, BOT_TAG_ENABLE)

    if random.random() < 0.3:
        await handle_who_request(message, WHO_REQUEST_ENABLE)
    else:
        logging.debug("Случайное условие не выполнено")

    await handle_maslina(message, MASLINA_ENABLE)

    # Если текст не проходит фильтрацию, дальнейшая обработка не требуется
    if not should_process_text(text):
        return

    keyword: str = extract_keyword(message)
    if not keyword:
        return

    results: list = find_links_by_keyword(keyword)
    if results:
        await process_results(message, results)
    else:
        logging.debug("Совпадений не найдено.")


def extract_keyword(message: Message) -> str:
    """
    Извлекает ключевое слово из сообщения.
    """
    if not message.text:
        logging.debug(f"Сообщение не содержит текста: {message}")
        return ""
    keyword: str = message.text.strip().lower()
    logging.debug(f"Извлечённое ключевое слово: {keyword}")
    return keyword


async def process_results(message: Message, results: list) -> None:
    """
    Обрабатывает результаты поиска ссылок.
    """
    filtered_results = (
        filter_recent_links(message.chat.id, results)
        if TIMEOUT_RESPONSES_ENABLE
        else results
    )

    if filtered_results:
        response: str = format_response(filtered_results)
        logging.debug(f"Отправка ссылки: {response}")
        # Кнопка лайк с начальным значением 0
        like_button = InlineKeyboardButton(text="👍 0", callback_data="like_init")
        # Кнопка дизлайк
        dislike_button = InlineKeyboardButton(text="👎 0", callback_data="dislike_init")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[like_button, dislike_button]], row_width=2)
        sent = await message.answer(response, reply_to_message_id=message.message_id, reply_markup=keyboard)
        # Инициализируем счётчики для отправленного сообщения
        reaction_counts[(sent.chat.id, sent.message_id)] = {"likes": 0, "dislikes": 0}
        # Обновляем callback_data, чтобы содержали реальные chat_id и message_id
        new_like_data = f"like:{sent.chat.id}:{sent.message_id}"
        new_dislike_data = f"dislike:{sent.chat.id}:{sent.message_id}"
        like_button = InlineKeyboardButton(text="👍 0", callback_data=new_like_data)
        dislike_button = InlineKeyboardButton(text="👎 0", callback_data=new_dislike_data)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[like_button, dislike_button]], row_width=2)
        await sent.edit_reply_markup(reply_markup=keyboard)

        # Планируем удаление ссылок из recent_links через таймаут
        if TIMEOUT_RESPONSES_ENABLE:
            for _, url in filtered_results:
                asyncio.create_task(remove_link_after_timeout(message.chat.id, url))
    else:
        logging.debug("Все ссылки уже были отправлены недавно.")


def filter_recent_links(chat_id: int, results: list) -> list:
    """
    Фильтрует ссылки, которые уже были отправлены недавно для конкретного чата.
    """
    filtered_results = []
    chat_recent_links = recent_links.setdefault(chat_id, {})
    for name, url in results:
        if (url in chat_recent_links
                and datetime.now() - chat_recent_links[url]
                < timedelta(minutes=TIMEOUT_MINUTES)):
            logging.debug(f"Пропуск отправки ссылки '{url}' "
                          f"для чата {chat_id} (отправлялась недавно).")
        else:
            filtered_results.append((name, url))
            chat_recent_links[url] = datetime.now()
    return filtered_results


def format_response(results: list) -> str:
    """
    Форматирует ответ для пользователя.
    """
    return ("Возможно это поможет разобраться:\n"
            + "\n".join([f"{name}: {url}" for name, url in results]))


async def remove_link_after_timeout(chat_id: int, url: str) -> None:
    """
    Удаляет ссылку из recent_links для конкретного чата через заданный таймаут.
    """
    await asyncio.sleep(TIMEOUT_MINUTES * 60)
    chat_recent_links = recent_links.get(chat_id, {})
    if url in chat_recent_links:
        del chat_recent_links[url]
        logging.debug(f"Ссылка '{url}' удалена из кэша для чата {chat_id}.")


async def handle_like_callback(callback_query: CallbackQuery) -> None:
    """
    Обработка нажатия на кнопку лайк.
    """
    data = callback_query.data  # формата "like:chat_id:message_id"
    _, chat_id_str, message_id_str = data.split(":")
    chat_id = int(chat_id_str)
    message_id = int(message_id_str)
    key = (chat_id, message_id)
    if key not in reaction_counts:
        await callback_query.answer()
        return
    # Увеличиваем счётчик лайков
    reaction_counts[key]["likes"] += 1
    likes = reaction_counts[key]["likes"]
    dislikes = reaction_counts[key]["dislikes"]
    # Получаем текущий объект сообщения
    msg = callback_query.message
    # Обновляем клавиатуру с новым значением лайков и дизлайков
    like_button = InlineKeyboardButton(text=f"👍 {likes}", callback_data=f"like:{chat_id}:{message_id}")
    dislike_button = InlineKeyboardButton(text=f"👎 {dislikes}", callback_data=f"dislike:{chat_id}:{message_id}")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[like_button, dislike_button]], row_width=2)
    await msg.edit_reply_markup(reply_markup=keyboard)
    await callback_query.answer("👍")


async def handle_dislike_callback(callback_query: CallbackQuery) -> None:
    """
    Обработка нажатия на кнопку дизлайк.
    """
    data = callback_query.data  # формата "dislike:chat_id:message_id"
    _, chat_id_str, message_id_str = data.split(":")
    chat_id = int(chat_id_str)
    message_id = int(message_id_str)
    key = (chat_id, message_id)
    if key not in reaction_counts:
        await callback_query.answer()
        return
    # Увеличиваем счётчик дизлайков
    reaction_counts[key]["dislikes"] += 1
    dislikes = reaction_counts[key]["dislikes"]
    likes = reaction_counts[key]["likes"]
    msg = callback_query.message
    # Если дизлайков стало больше, чем лайков — удаляем сообщение
    if dislikes > likes:
        await msg.delete()
        # Удаляем записи из хранилищ
        reaction_counts.pop(key, None)
        recent_links.get(chat_id, {}).pop(msg.text, None)
        await callback_query.answer("Сообщение удалено")
    else:
        # Обновляем клавиатуру с новыми значениями лайков и дизлайков
        like_button = InlineKeyboardButton(text=f"👍 {likes}", callback_data=f"like:{chat_id}:{message_id}")
        dislike_button = InlineKeyboardButton(text=f"👎 {dislikes}", callback_data=f"dislike:{chat_id}:{message_id}")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[like_button, dislike_button]], row_width=2)
        await msg.edit_reply_markup(reply_markup=keyboard)
        await callback_query.answer("👎")


async def no_fsm_filter(message: Message, state: FSMContext) -> bool:
    """
    Фильтр для обработки сообщений, только если
    у пользователя отсутствует активное FSM-состояние.
    """
    current_state = await state.get_state()
    return ((current_state is None)
            and bool(message.text)
            and (not message.text.startswith("/")))


def register_message_handlers(dp) -> None:
    """
    Регистрирует глобальный обработчик сообщений.
    """
    dp.message.register(handle_message, no_fsm_filter)
    dp.callback_query.register(handle_like_callback, lambda c: c.data and c.data.startswith("like:"))
    dp.callback_query.register(handle_dislike_callback, lambda c: c.data and c.data.startswith("dislike:"))
