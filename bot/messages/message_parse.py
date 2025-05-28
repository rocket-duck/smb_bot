import re
import logging
from bot.config.links import LINKS

from typing import List, Tuple

def should_skip(keyword: str) -> bool:
    """
    Определяет, нужно ли пропустить выдачу ссылок для статусных или негативных вопросов.
    """
    lower = keyword.lower()
    # Статусные вопросы о работоспособности или жизненном цикле
    if "не работает" in lower or "умер" in lower or "мерт" in lower or "жива" in lower:
        return True
    # Вопросы о работоспособности без слова 'как'
    if re.search(r"\bработает\b", lower) and "как" not in lower:
        return True
    return False

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)


def find_links_by_keyword(keyword):
    """
    Функция для поиска ссылок по ключевому слову в структуре LINKS.
    :param keyword: Ключевое слово для поиска
    :return: Список кортежей (название, ссылка), соответствующих ключевому слову
    """
    keyword = keyword.strip().lower()
    # Пропускаем прямые статусные вопросы
    if should_skip(keyword):
        logging.debug(f"Пропускаем запрос на статус: {keyword}")
        return []
    logging.debug(f"Поиск по ключевому слову: {keyword}")
    raw_results: List[Tuple[str, str]] = []

    # Запускаем рекурсивный поиск
    _recursive_search(LINKS, keyword, raw_results)

    return raw_results[:3]


def _recursive_search(data, keyword, results, parent_name=""):
    """
    Рекурсивный поиск по структуре LINKS.
    :param data: Текущая структура данных
    :param keyword: Ключевое слово для поиска
    :param results: Список результатов
    :param parent_name: Имя родительского раздела
    """
    for key, value in data.items():
        if _is_section(value):
            _process_section(key, value, keyword, results)
        elif _has_subsections(value):
            section_name = _build_section_name(parent_name, key)
            _recursive_search(value["subsections"],
                              keyword,
                              results,
                              section_name)


def _is_section(value):
    """
    Проверяет, является ли элемент разделом с URL и регулярными выражениями.
    :param value: Проверяемое значение
    :return: True, если это раздел; иначе False
    """
    return isinstance(value, dict) and "url" in value and "regex" in value


def _has_subsections(value):
    """
    Проверяет, есть ли у элемента вложенные подразделы.
    :param value: Проверяемое значение
    :return: True, если есть вложенные подразделы; иначе False
    """
    return isinstance(value, dict) and "subsections" in value


def _process_section(key, value, keyword, results):
    """
    Обрабатывает текущий раздел и
    проверяет совпадение с регулярными выражениями.
    :param key: Название раздела
    :param value: Данные раздела
    :param keyword: Ключевое слово для поиска
    :param results: Список результатов
    """
    if is_match(keyword, value.get("regex", [])):
        logging.debug(f"Найдено совпадение: {key} -> {value['url']}")
        results.append((key, value["url"]))


def _build_section_name(parent_name, key):
    """
    Строит имя текущего раздела с учётом родительского имени.
    :param parent_name: Имя родительского раздела
    :param key: Текущий ключ
    :return: Полное имя раздела
    """
    return parent_name + f" > {key}" if parent_name else key


def is_match(keyword, regex_list):
    """
    Проверяет, соответствует ли ключевое слово
    хотя бы одному из регулярных выражений.
    :param keyword: Ключевое слово
    :param regex_list: Список регулярных выражений
    :return: True, если есть совпадение; иначе False
    """
    return any(re.search(regex, keyword, re.IGNORECASE) for regex in regex_list)
