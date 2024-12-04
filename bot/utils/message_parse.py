import re
import logging
from bot.config.links import LINKS

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

def find_links_by_keyword(keyword):
    """
    Функция для поиска ссылок по ключевому слову.

    :param keyword: Ключевое слово для поиска
    :return: Список кортежей (название, ссылка), соответствующих ключевому слову
    """
    results = []
    keyword = keyword.strip().lower()
    logging.debug(f"Поиск по ключевому слову: {keyword}")
    logging.debug(f"Словарь LINKS: {LINKS}")

    for section, content in LINKS.items():
        # Если content — словарь с вложенными элементами
        if isinstance(content, dict) and all(isinstance(v, dict) for v in content.values()):
            for sub_key, sub_value in content.items():
                url = sub_value.get("url")
                regex_list = sub_value.get("regex", [])
                if is_match(keyword, regex_list, sub_key):
                    logging.debug(f"Найдено совпадение: {sub_key} -> {url}")
                    results.append((sub_key, url))
        # Если content — отдельная запись
        elif isinstance(content, dict):
            url = content.get("url")
            regex_list = content.get("regex", [])
            if is_match(keyword, regex_list, section):
                logging.debug(f"Найдено совпадение: {section} -> {url}")
                results.append((section, url))

    if not results:
        logging.debug("Совпадений не найдено.")
    return results


def is_match(keyword, regex_list, text):
    """
    Проверяет, соответствует ли ключевое слово хотя бы одному из регулярных выражений или названию текста.

    :param keyword: Ключевое слово
    :param regex_list: Список регулярных выражений
    :param text: Текст для проверки
    :return: True, если есть совпадение; иначе False
    """
    # Проверяем по регулярным выражениям
    for regex in regex_list:
        if re.search(regex, keyword, re.IGNORECASE):
            return True
    # Проверяем на точное совпадение
    return text.lower() == keyword
