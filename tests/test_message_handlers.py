import pytest

from bot.content.dicts_loader import load_errors, load_links
from bot.messages.message_parse import find_links_by_keyword, parse_error_codes
from bot.messages.messages import format_response

_links = load_links()
_errors = load_errors()

# Только ключи из links, у которых есть прямое поле 'url' или 'bot'
VALID_LINK_KEYS = [k for k, v in _links.items() if "url" in v or "bot" in v]


# 1) Тестируем, что каждый код из errors парсится:
@pytest.mark.parametrize("code,description", _errors)
def test_parse_error_codes_exact_match(code, description):
    matches = parse_error_codes(code, True)
    assert (code, description) in matches, (
        f"Парсер должен найти {(code, description)}, " f"а нашёл {matches}"
    )


# 2) Тестируем, что поиск по каждому ключевому слову из LINKS не даёт пустого списка:


@pytest.mark.parametrize("keyword", VALID_LINK_KEYS)
def test_find_links_by_keyword_returns_results(keyword):
    results = find_links_by_keyword(keyword, True)
    assert isinstance(results, list)
    assert results, f"По ключу '{keyword}' не найдено ни одной ссылки"


# 3) Проверяем, что форматирование ответа включает все переданные пары:


def test_format_response_structure():
    sample = [("First", "http://example.com/1"), ("Second", "http://ex.com/2")]
    resp = format_response(sample)
    # Должно начинаться с заголовка
    assert resp.startswith("Возможно это поможет разобраться:\n")
    # И содержать все имена и URL
    assert "First: http://example.com/1" in resp
    assert "Second: http://ex.com/2" in resp
