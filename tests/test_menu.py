import pytest
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.services.menu_service import create_menu
from bot.config.links import LINKS

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
    expected_count = len(LINKS)
    assert len(keyboard.inline_keyboard) == expected_count
    for row in keyboard.inline_keyboard:
        assert isinstance(row, list) and len(row) == 1
        button = row[0]
        assert isinstance(button, InlineKeyboardButton)
        assert button.url or button.callback_data

def test_create_menu_submenu_buttons_and_back():
    parent_item = next((item for item in LINKS.values() if item.get("subsections")), None)
    assert parent_item is not None, "No section with subsections found in LINKS"
    parent_key = parent_item["key"]
    user_id = 12345
    keyboard, title = create_menu(parent_key, user_id)
    subsections = parent_item["subsections"]
    # submenu buttons count = number of subsections + back button
    assert len(keyboard.inline_keyboard) == len(subsections) + 1
    back_button = keyboard.inline_keyboard[-1][0]
    assert "Назад" in back_button.text
    assert back_button.callback_data.endswith(":main")
