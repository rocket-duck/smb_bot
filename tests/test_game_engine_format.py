import pytest

from bot.utils.game_engine import format_declension, format_winner_mention


@pytest.mark.parametrize(
    "wins,expected",
    [
        (1, "победа"),
        (2, "победы"),
        (5, "побед"),
        (11, "побед"),
    ],
)
def test_format_declension(wins, expected):
    assert format_declension(wins) == expected


def test_format_winner_mention():
    assert (
        format_winner_mention("1", "User")
        == '<a href="tg://user?id=1">User</a>'
    )
