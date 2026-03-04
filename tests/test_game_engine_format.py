import pytest

from bot.utils.game_engine import format_declension, format_winner_mention


@pytest.mark.parametrize(
    "wins,expected",
    [
        (1, "победа"),
        (2, "победы"),
        (3, "победы"),
        (4, "победы"),
        (5, "побед"),
        (11, "побед"),
        (12, "побед"),
        (13, "побед"),
        (14, "побед"),
        (21, "победа"),
        (22, "победы"),
        (100, "побед"),
        (101, "победа"),
        (111, "побед"),
    ],
)
def test_format_declension(wins, expected):
    assert format_declension(wins) == expected


def test_format_winner_mention():
    result = format_winner_mention(12345, "Alice")
    assert result == '<a href="tg://user?id=12345">Alice</a>'
