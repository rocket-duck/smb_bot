from __future__ import annotations

import json
import logging
from pathlib import Path

_DATA_DICTS_DIR = Path("data") / "dicts"


def _load_json(filename: str):
    path = _DATA_DICTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Файл словаря не найден: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_triggers() -> list[str]:
    try:
        return _load_json("who_request.json")["triggers"]
    except Exception as exc:
        logging.warning("Не удалось загрузить триггеры who_request: %s", exc)
        return []


def load_errors() -> list[tuple[str, str]]:
    try:
        return [tuple(item) for item in _load_json("errors.json")]
    except Exception as exc:
        logging.warning("Не удалось загрузить словарь ошибок: %s", exc)
        return []


def load_links() -> dict:
    try:
        return _load_json("links.json")
    except Exception as exc:
        logging.warning("Не удалось загрузить словарь ссылок: %s", exc)
        return {}


def load_dushnila_phrases() -> tuple[list[tuple[str, int]], list[tuple[str, int]]]:
    try:
        data = _load_json("dushnila_phrases.json")
        positive = [tuple(item) for item in data["positive"]]
        negative = [tuple(item) for item in data["negative"]]
        return positive, negative
    except Exception as exc:
        logging.warning("Не удалось загрузить словарь фраз душнилы: %s", exc)
        return [], []
