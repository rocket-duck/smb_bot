import pytest
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.services.menu_service import create_menu
from bot.config.links import LINKS
import itertools

@pytest.mark.parametrize("menu_key,expected_title", [
    (None, "Главное меню"),
    ("dostupy", "Доступы"),
])
def test_create_menu_titles(menu_key, expected_title):
    user_id = 12345
    keyboard, title = create_menu(menu_key, user_id)
    assert isinstance(keyboard, InlineKeyboardMarkup)
    assert title == expected_title

def test_create_menu_main_buttons_count():
    user_id = 12345
    keyboard, title = create_menu(None, user_id)
    # Expected: one button per unique category plus direct links for entries without a path
    category_count = len({entry["path"][0] for entry in LINKS if entry.get("path")})
    no_path_count = sum(1 for entry in LINKS if not entry.get("path"))
    expected_count = category_count + no_path_count
    assert len(keyboard.inline_keyboard) == expected_count
    for row in keyboard.inline_keyboard:
        assert isinstance(row, list) and len(row) == 1
        button = row[0]
        assert isinstance(button, InlineKeyboardButton)
        assert button.url or button.callback_data

def test_create_menu_submenu_buttons_and_back():
    # Pick a category slug from LINKS
    slugs = {entry["id"].split(".", 1)[0] for entry in LINKS if entry.get("path")}
    parent_key = next(iter(slugs))
    # Determine display name for this category
    display_name = next(
        entry["path"][0] for entry in LINKS if entry["id"].split(".", 1)[0] == parent_key
    )
    user_id = 12345
    keyboard, title = create_menu(parent_key, user_id)
    # Number of links in this category
    count = sum(
        1 for entry in LINKS if entry["id"].split(".", 1)[0] == parent_key
    )
    # submenu buttons count = number of links + back button
    assert title == display_name
    assert len(keyboard.inline_keyboard) == count + 1
    back_button = keyboard.inline_keyboard[-1][0]
    assert "Назад" in back_button.text
    assert back_button.callback_data.endswith(":main")
