from aiogram.types import Message
from bot.utils.message_parse import find_links_by_keyword
import logging

async def handle_message(message: Message):
    """
    Обрабатывает текстовые сообщения для поиска по ключевым словам.

    :param message: Сообщение от пользователя
    """
    logging.debug(f"Получено сообщение: {message.text}")
    keyword = message.text.strip().lower()

    # Поиск ссылок по ключевому слову
    results = find_links_by_keyword(keyword)
    if results:
        response = "Вот что я нашёл:\n" + "\n".join([f"{name}: {link}" for name, link in results])
        logging.debug(f"Отправка ссылки: {response}")
        await message.answer(response)

def register_message_handlers(dp):
    """
    Регистрирует обработчик текстовых сообщений.

    :param dp: Экземпляр Dispatcher
    """
    dp.message.register(handle_message)