from pathlib import Path

import pytest

from bot.content.good_morning_content import (
    list_morning_images,
    load_morning_phrases,
)


def test_load_morning_phrases_valid(tmp_path: Path):
    phrases_file = tmp_path / "phrases.json"
    phrases_file.write_text('{"phrases":[" hi ", "there"]}', encoding="utf-8")

    phrases = load_morning_phrases(phrases_file)

    assert phrases == ["hi", "there"]


def test_load_morning_phrases_invalid(tmp_path: Path):
    phrases_file = tmp_path / "phrases.json"
    phrases_file.write_text('{"phrases": "nope"}', encoding="utf-8")

    with pytest.raises(ValueError):
        load_morning_phrases(phrases_file)


def test_list_morning_images_filters_extensions(tmp_path: Path):
    (tmp_path / "a.jpg").write_bytes(b"a")
    (tmp_path / "b.PNG").write_bytes(b"b")
    (tmp_path / "c.txt").write_text("skip", encoding="utf-8")

    files = list_morning_images(tmp_path)

    assert sorted(files) == ["a.jpg", "b.PNG"]
