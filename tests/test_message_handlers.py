import pytest

from bot.messages.message_parse import parse_error_codes, find_links_by_keyword
from bot.messages.messages import format_response
from bot.dicts.errors import raw_errors
from bot.dicts.links import LINKS

# Только ключи из LINKS, у которых есть прямое поле 'url' или 'bot'
VALID_LINK_KEYS = [k for k, v in LINKS.items() if 'url' in v or 'bot' in v]

# 1) Тестируем, что каждый код из raw_errors парсится:
@pytest.mark.parametrize("code,description", raw_errors)
def test_parse_error_codes_exact_match(code, description):
    matches = parse_error_codes(code)
    assert (code, description) in matches, (
        f"Парсер должен найти {(code, description)}, "
        f"а нашёл {matches}"
    )

# 2) Тестируем, что поиск по каждому ключевому слову из LINKS не даёт пустого списка:
@pytest.mark.parametrize("keyword", VALID_LINK_KEYS)
def test_find_links_by_keyword_returns_results(keyword):
    results = find_links_by_keyword(keyword)
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
