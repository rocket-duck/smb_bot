"""Unit tests for pure scoring functions in bot/utils/dushnila_engine.py."""

from datetime import datetime
from types import SimpleNamespace

from bot.utils import dushnila_engine as engine

# ── score_phrases ────────────────────────────────────────────────────────────


def test_score_phrases_matches_positive_phrase():
    events = engine.score_phrases("а если это не сработает?", [("а если", 2)], "phrase")
    assert events == [("phrase", "фраза «а если»", 2)]


def test_score_phrases_no_match():
    events = engine.score_phrases("всё супер", [("а если", 2)], "phrase")
    assert events == []


def test_score_phrases_case_insensitive():
    events = engine.score_phrases("ЭТО БАГ, однозначно", [("это баг", 5)], "phrase")
    assert events == [("phrase", "фраза «это баг»", 5)]


def test_score_phrases_anti_matches_standalone():
    events = engine.score_phrases("согласен, поехали", [("согласен", -3)], "anti")
    assert events == [("anti", "фраза «согласен»", -3)]


def test_score_phrases_anti_does_not_match_when_negated():
    """'не согласен' не должно триггерить анти-фразу 'согласен'."""
    events = engine.score_phrases(
        "я не согласен с этим решением", [("согласен", -3)], "anti"
    )
    assert events == []


def test_not_soglasen_scores_only_as_positive_phrase():
    positive = [("не согласен", 3)]
    negative = [("согласен", -3)]
    content = "я не согласен с этим решением"
    pos_events = engine.score_phrases(content, positive, "phrase")
    neg_events = engine.score_phrases(content, negative, "anti")
    assert pos_events == [("phrase", "фраза «не согласен»", 3)]
    assert neg_events == []


# ── score_length ─────────────────────────────────────────────────────────────


def test_score_length_below_smallest_tier():
    assert engine.score_length("короткое сообщение") == []


def test_score_length_sums_all_crossed_tiers():
    content = "x" * 3200
    events = engine.score_length(content)
    assert events == [
        ("length", "300+ символов", 2),
        ("length", "700+ символов", 5),
        ("length", "1500+ символов", 10),
        ("length", "3000+ символов", 20),
    ]


def test_score_length_single_tier():
    content = "x" * 350
    events = engine.score_length(content)
    assert events == [("length", "300+ символов", 2)]


# ── score_questions ──────────────────────────────────────────────────────────


def test_score_questions_no_question_mark():
    assert engine.score_questions("просто текст") == []


def test_score_questions_single_question():
    events = engine.score_questions("работает?")
    assert events == [("question", "в сообщении есть вопрос", 1)]


def test_score_questions_sums_tiers_above_three():
    content = "???" + "?"  # 4 question marks
    events = engine.score_questions(content)
    assert events == [
        ("question", "в сообщении есть вопрос", 1),
        ("question", "4 вопросов в сообщении", 5),
    ]


def test_score_questions_sums_all_tiers_above_seven():
    content = "?" * 8
    events = engine.score_questions(content)
    assert events == [
        ("question", "в сообщении есть вопрос", 1),
        ("question", "8 вопросов в сообщении", 5),
        ("question", "8 вопросов в сообщении", 12),
    ]


# ── score_media ──────────────────────────────────────────────────────────────


def test_score_media_photo_only():
    message = SimpleNamespace(photo=[object()], video=None, caption=None)
    assert engine.score_media(message) == [("media", "прислал скрин", 2)]


def test_score_media_video_short_caption():
    message = SimpleNamespace(photo=None, video=object(), caption="короткая подпись")
    assert engine.score_media(message) == [("media", "прислал видео", 4)]


def test_score_media_video_with_long_caption_stacks():
    message = SimpleNamespace(photo=None, video=object(), caption="x" * 300)
    events = engine.score_media(message)
    assert events == [
        ("media", "прислал видео", 4),
        ("media", "видео с длинным описанием", 8),
    ]


def test_score_media_no_attachment():
    message = SimpleNamespace(photo=None, video=None, caption=None)
    assert engine.score_media(message) == []


# ── score_evening ────────────────────────────────────────────────────────────


def test_score_evening_daytime_no_bonus():
    dt = datetime(2026, 7, 27, 14, 0)
    assert engine.score_evening(dt) == []


def test_score_evening_after_twenty():
    dt = datetime(2026, 7, 27, 21, 0)
    assert engine.score_evening(dt) == [("evening", "сообщение после 20:00", 2)]


def test_score_evening_after_twentytwo_stacks():
    dt = datetime(2026, 7, 27, 23, 0)
    events = engine.score_evening(dt)
    assert events == [
        ("evening", "сообщение после 20:00", 2),
        ("evening", "сообщение после 22:00", 5),
    ]


def test_score_evening_after_midnight_only():
    dt = datetime(2026, 7, 28, 2, 0)
    assert engine.score_evening(dt) == [("evening", "сообщение после полуночи", 10)]


# ── score_streak ─────────────────────────────────────────────────────────────


def test_score_streak_fires_only_on_exact_thresholds():
    assert engine.score_streak(1) is None
    assert engine.score_streak(2) is None
    assert engine.score_streak(3) == ("streak", "3 сообщений подряд", 2)
    assert engine.score_streak(4) is None
    assert engine.score_streak(5) == ("streak", "5 сообщений подряд", 5)
    assert engine.score_streak(9) is None
    assert engine.score_streak(10) == ("streak", "10 сообщений подряд", 15)
    assert engine.score_streak(11) is None


# ── level_for_score ──────────────────────────────────────────────────────────


def test_level_for_score_boundaries():
    assert engine.level_for_score(-10) == "😇 Спокойный тестировщик"
    assert engine.level_for_score(0) == "😇 Спокойный тестировщик"
    assert engine.level_for_score(19) == "😇 Спокойный тестировщик"
    assert engine.level_for_score(20) == "🙂 Лёгкая душность"
    assert engine.level_for_score(69) == "🤓 Душнила"
    assert engine.level_for_score(70) == "🧐 Старший душнила"
    assert engine.level_for_score(199) == "👑 Главный душнила"
    assert engine.level_for_score(200) == "🧠 Легенда душности"
    assert engine.level_for_score(1000) == "🧠 Легенда душности"


# ── format_points_declension ─────────────────────────────────────────────────


def test_format_points_declension():
    assert engine.format_points_declension(1) == "балл"
    assert engine.format_points_declension(21) == "балл"
    assert engine.format_points_declension(2) == "балла"
    assert engine.format_points_declension(4) == "балла"
    assert engine.format_points_declension(5) == "баллов"
    assert engine.format_points_declension(11) == "баллов"
    assert engine.format_points_declension(0) == "баллов"
    assert engine.format_points_declension(-2) == "балла"
