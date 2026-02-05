import logging
import random

from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import bot.config.flags as flag
from bot.config.settings import get_settings
from bot.messages.bot_tag import handle_bot_tag
from bot.messages.help_epa_message import get_auth_issue_response
from bot.messages.maslina import handle_maslina
from bot.messages.message_parse import find_links_by_keyword, parse_error_codes
from bot.messages.who_request import handle_who_request, is_who_request_trigger
from bot.storage.cache import cache
from bot.utils.participants import update_participant

REACTION_TTL_SECONDS = 24 * 60 * 60
settings = get_settings()


def should_process_text(text: str) -> bool:
    """
    Возвращает True, если текст сообщения должен быть обработан.
    Проверяются:
      - Если текст ровно равен упоминанию бота
      - Если сообщение начинается со слеша (команда)
      - Если функция парсинга сообщений отключена
    """
    if should_ignore_bot_mention(text, settings.bot_username):
        logging.debug("Сообщение равно упоминанию бота, обработка прекращена.")
        return False
    if text.startswith("/"):
        logging.debug(f"Сообщение {text} игнорируется, так как это команда.")
        return False
    if not flag.KEYWORD_RESPONSES_ENABLE:
        logging.debug("Функция парсинга сообщений отключена")
        return False
    return True


def should_ignore_bot_mention(text: str, bot_username) -> bool:
    """
    Возвращает True, если текст сообщения ровно равен упоминанию бота.
    """
    normalized_username = (
        bot_username[0] if isinstance(bot_username, tuple) else bot_username
    )
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
    await update_participant(message)

    # Обработка дополнительных фановых триггеров
    await handle_bot_tag(message, settings.bot_username, flag.BOT_TAG_ENABLE)

    # Бросаем два кубика d20: бот и пользователь
    if flag.WHO_REQUEST_ENABLE:
        if not message.text or not is_who_request_trigger(message.text.lower()):
            logging.debug("who_request: триггер не найден, бросок кубиков не нужен")
        else:
            bot_roll = random.randint(1, 20)
            user_roll = random.randint(1, 20)
            logging.debug(
                f"Кубики who_request: пользователь={user_roll}, бот={bot_roll}"
            )
            if user_roll == 1:
                if flag.FORCE_BESTOLOCH_ENABLE:
                    await handle_who_request(
                        message,
                        flag.WHO_REQUEST_ENABLE,
                        force_bestoloch_enable=True,
                        user_roll=user_roll,
                        bot_roll=bot_roll,
                    )
                else:
                    await handle_who_request(
                        message,
                        flag.WHO_REQUEST_ENABLE,
                        user_roll=user_roll,
                        bot_roll=bot_roll,
                    )
            elif user_roll == 20 or (user_roll > 1 and user_roll >= bot_roll):
                await handle_who_request(
                    message,
                    flag.WHO_REQUEST_ENABLE,
                    user_roll=user_roll,
                    bot_roll=bot_roll,
                )
            else:
                logging.debug("Условие бросков кубиков не выполнено")
    else:
        logging.debug("Флаг WHO_REQUEST_ENABLE выключен, пропускаем who_request")

    await handle_maslina(message, flag.MASLINA_ENABLE)
    # Проверка общих проблем авторизации
    help_msg = get_auth_issue_response(text, flag.HELP_EPA_MESSAGE_ENABLE)
    if help_msg:
        await message.reply(help_msg)
        return

    # Если текст не проходит фильтрацию, дальнейшая обработка не требуется
    if not should_process_text(text):
        return

    keyword: str = extract_keyword(message)
    if not keyword:
        return

    # Парсим коды ошибок и отправляем сообщения об ошибках, если найдены
    error_matches = parse_error_codes(keyword, flag.ERRORS_PARSE_ENABLE)
    if error_matches:
        for code, description in error_matches:
            await message.reply(f"Ошибка {code}: {description}")
        return

    results: list = find_links_by_keyword(keyword, flag.ERRORS_PARSE_ENABLE)
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
        await filter_recent_links(message.chat.id, results)
        if flag.TIMEOUT_RESPONSES_ENABLE
        else results
    )

    if filtered_results:
        response: str = format_response(filtered_results)
        logging.debug(f"Отправка ссылки: {response}")
        like_button = InlineKeyboardButton(text="👍 0", callback_data="like_init")
        dislike_button = InlineKeyboardButton(text="👎 0", callback_data="dislike_init")
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[like_button, dislike_button]], row_width=2
        )
        sent = await message.answer(
            response, reply_to_message_id=message.message_id, reply_markup=keyboard
        )
        await cache.init_reaction(sent.chat.id, sent.message_id, REACTION_TTL_SECONDS)
        new_like_data = f"like:{sent.chat.id}:{sent.message_id}"
        new_dislike_data = f"dislike:{sent.chat.id}:{sent.message_id}"
        like_button = InlineKeyboardButton(text="👍 0", callback_data=new_like_data)
        dislike_button = InlineKeyboardButton(
            text="👎 0", callback_data=new_dislike_data
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[like_button, dislike_button]], row_width=2
        )
        await sent.edit_reply_markup(reply_markup=keyboard)
    else:
        logging.debug("Все ссылки уже были отправлены недавно.")


async def filter_recent_links(chat_id: int, results: list) -> list:
    """
    Фильтрует ссылки, которые уже были отправлены недавно для конкретного чата.
    """
    filtered_results = []
    for name, url in results:
        if await cache.is_recent_link(chat_id, url):
            logging.debug(
                f"Пропуск отправки ссылки '{url}' для чата {chat_id} (отправлялась недавно)."
            )
        else:
            filtered_results.append((name, url))
            await cache.set_recent_link(chat_id, url, flag.TIMEOUT_MINUTES * 60)
    return filtered_results


def format_response(results: list) -> str:
    """
    Форматирует ответ для пользователя.
    """
    return "Возможно это поможет разобраться:\n" + "\n".join(
        [f"{name}: {url}" for name, url in results]
    )


async def handle_like_callback(callback_query: CallbackQuery) -> None:
    """
    Обработка нажатия на кнопку лайк.
    """
    data = callback_query.data  # формата "like:chat_id:message_id"
    _, chat_id_str, message_id_str = data.split(":")
    chat_id = int(chat_id_str)
    message_id = int(message_id_str)
    if not await cache.get_reaction(chat_id, message_id):
        await callback_query.answer()
        return
    likes, dislikes = await cache.increment_reaction(
        chat_id, message_id, "like", REACTION_TTL_SECONDS
    )
    msg = callback_query.message
    like_button = InlineKeyboardButton(
        text=f"👍 {likes}", callback_data=f"like:{chat_id}:{message_id}"
    )
    dislike_button = InlineKeyboardButton(
        text=f"👎 {dislikes}", callback_data=f"dislike:{chat_id}:{message_id}"
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[like_button, dislike_button]], row_width=2
    )
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
    if not await cache.get_reaction(chat_id, message_id):
        await callback_query.answer()
        return
    likes, dislikes = await cache.increment_reaction(
        chat_id, message_id, "dislike", REACTION_TTL_SECONDS
    )
    msg = callback_query.message
    if dislikes > likes:
        await msg.delete()
        await cache.remove_reaction(chat_id, message_id)
        await callback_query.answer("Сообщение удалено")
    else:
        like_button = InlineKeyboardButton(
            text=f"👍 {likes}", callback_data=f"like:{chat_id}:{message_id}"
        )
        dislike_button = InlineKeyboardButton(
            text=f"👎 {dislikes}", callback_data=f"dislike:{chat_id}:{message_id}"
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[like_button, dislike_button]], row_width=2
        )
        await msg.edit_reply_markup(reply_markup=keyboard)
        await callback_query.answer("👎")


async def no_fsm_filter(message: Message, state: FSMContext) -> bool:
    """
    Фильтр для обработки сообщений, только если
    у пользователя отсутствует активное FSM-состояние.
    """
    current_state = await state.get_state()
    return (
        (current_state is None)
        and bool(message.text)
        and (not message.text.startswith("/"))
    )


def register_message_handlers(dp) -> None:
    """
    Регистрирует глобальный обработчик сообщений.
    """
    dp.message.register(handle_message, no_fsm_filter)
    dp.callback_query.register(
        handle_like_callback, lambda c: c.data and c.data.startswith("like:")
    )
    dp.callback_query.register(
        handle_dislike_callback, lambda c: c.data and c.data.startswith("dislike:")
    )
