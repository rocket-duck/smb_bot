from __future__ import annotations

import json
from pathlib import Path

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def load_morning_phrases(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Ожидался JSON-объект с ключом 'phrases'.")
    phrases = data.get("phrases")
    if not isinstance(phrases, list):
        raise ValueError("Поле 'phrases' должно быть списком строк.")
    cleaned = [str(item).strip() for item in phrases if str(item).strip()]
    if not cleaned:
        raise ValueError("Список фраз пуст.")
    return cleaned


def list_morning_images(images_dir: Path) -> list[str]:
    if not images_dir.is_dir():
        return []
    return [
        path.name
        for path in images_dir.iterdir()
        if path.is_file() and path.suffix.lower() in ALLOWED_IMAGE_EXTENSIONS
    ]
