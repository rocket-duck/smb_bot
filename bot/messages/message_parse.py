import re
import logging
from bot.config.links import LINKS

import numpy as np
from sentence_transformers import SentenceTransformer
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

# Initialize semantic search model on CPU to avoid MPS tensors
_semantic_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')

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
    raw_results: List[Tuple[str, str, float]] = []

    # Запускаем рекурсивный поиск
    _recursive_search(LINKS, keyword, raw_results)

    # Сортируем результаты по семантической схожести и фильтруем по порогу
    sorted_results = sorted(raw_results, key=lambda x: x[2], reverse=True)
    filtered = [(k, u) for k, u, s in sorted_results if s >= 0.6][:3]
    if not filtered:
        logging.debug("Совпадений не найдено.")
    return filtered


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


def _process_section(key, value, keyword, raw_results):
    """
    Обрабатывает текущий раздел и
    проверяет совпадение с регулярными выражениями.
    :param key: Название раздела
    :param value: Данные раздела
    :param keyword: Ключевое слово для поиска
    :param raw_results: Список результатов с семантической оценкой
    """
    # сначала проверяем по регуляркам, затем семантически по названию раздела
    if semantic_match(keyword, key):
        sim_score = semantic_score(keyword, key)
        logging.debug(f"Найдено совпадение: {key} ({sim_score:.2f}) -> {value['url']}")
        raw_results.append((key, value["url"], sim_score))


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


def semantic_score(query: str, text: str) -> float:
    """
    Возвращает семантическую схожесть (косинус) между запросом и текстом.
    """
    q_emb = _semantic_model.encode(query, convert_to_numpy=True)
    t_emb = _semantic_model.encode(text, convert_to_numpy=True)
    # Если тензоры, переместить на CPU и в numpy
    if hasattr(q_emb, "cpu"):
        q_emb = q_emb.cpu().numpy()
    if hasattr(t_emb, "cpu"):
        t_emb = t_emb.cpu().numpy()
    sim = np.dot(q_emb, t_emb) / (np.linalg.norm(q_emb) * np.linalg.norm(t_emb))
    return float(sim)


def semantic_match(query: str, text: str, threshold: float = 0.7) -> bool:
    """
    Проверяет семантическое сходство между запросом и текстом.
    :param query: Текст пользователя
    :param text: Название раздела или описание
    :param threshold: Порог сходства для срабатывания
    :return: True, если сходство >= threshold
    """
    return semantic_score(query, text) >= threshold
