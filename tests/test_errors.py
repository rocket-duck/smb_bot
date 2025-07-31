import re
import pytest
from bot.dicts.errors import errors

@pytest.mark.parametrize("code,variants,negatives", [
    # код, варианты, которые должны совпадать, и один «левый» пример
    ("B0101",
     ["B0101", "b0101", "В0101", "в0101", "0101"],
     ["X0101"]
    ),
    ("C0402",
     ["C0402", "c0402", "С0402", "с0402", "0402"],
     ["Y0402"]
    ),
    ("A0001",
     ["A0001", "a0001", "А0001", "а0001", "0001"],
     ["Z0001"]
    ),
    ("v2_B0710",
     ["v2_B0710", "V2_b0710", "v2_b0710", "B0710", "0710"],
     ["v2_X0710"]
    ),
])
def test_code_regex_matches_and_not(code, variants, negatives):
    # Найдём нужный словарь по полю "code"
    entry = next(e for e in errors if e["code"] == code)
    pattern = re.compile(entry["regex"])

    # Проверяем все допустимые варианты
    for text in variants:
        assert pattern.search(text), (
            f"Pattern for {code!r} should match {text!r}, regex={entry['regex']}"
        )

    # И уверяемся, что «левые» строки не совпадают
    for bad in negatives:
        assert not pattern.search(bad), (
            f"Pattern for {code!r} should NOT match {bad!r}, regex={entry['regex']}"
        )
