import logging
import re
from datetime import UTC, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from bot.config import flags
from bot.config.settings import get_settings
from bot.content.dicts_loader import load_dushnila_phrases
from bot.database import SessionLocal
from bot.models import DushnilaEvent, DushnilaStreak, DushnilaWeekReset, Participant
from bot.utils.good_morning import MOSCOW_TZ

logger = logging.getLogger(__name__)

LONG_CAPTION_THRESHOLD = 300

LENGTH_TIERS = [(300, 2), (700, 5), (1500, 10), (3000, 20)]
STREAK_TIERS = {3: 2, 5: 5, 10: 15}

LEVELS = [
    (0, "😇 Спокойный тестировщик"),
    (20, "🙂 Лёгкая душность"),
    (40, "🤓 Душнила"),
    (70, "🧐 Старший душнила"),
    (120, "👑 Главный душнила"),
    (200, "🧠 Легенда душности"),
]


# ── Pure scoring functions ──────────────────────────────────────────────────


def level_for_score(score: int) -> str:
    """Возвращает эмодзи-уровень для набранных баллов."""
    level = LEVELS[0][1]
    for threshold, name in LEVELS:
        if score >= threshold:
            level = name
    return level


def format_display_name(full_name: str, username: str) -> str:
    """Возвращает 'Имя (username)' без @ перед username; без скобок, если его нет."""
    return f"{full_name} ({username})" if username else full_name


def format_points_declension(points: int) -> str:
    """Возвращает правильную форму слова 'балл' в зависимости от числа points."""
    n = abs(points)
    if n % 10 == 1 and n % 100 != 11:
        return "балл"
    elif n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return "балла"
    else:
        return "баллов"


def score_phrases(
    content: str, phrases: list[tuple[str, int]], category: str
) -> list[tuple[str, str, int]]:
    """Ищет фразы из словаря в тексте сообщения.

    Для category="anti" совпадение пропускается, если фразе непосредственно
    предшествует "не " — иначе "не согласен" (+3) всегда гасился бы вложенной
    в него анти-фразой "согласен" (-3).
    """
    content_lower = content.lower()
    events: list[tuple[str, str, int]] = []
    for phrase, points in phrases:
        phrase_lower = phrase.lower()
        if category == "anti":
            pattern = r"(?<!не )" + re.escape(phrase_lower)
            matched = re.search(pattern, content_lower) is not None
        else:
            matched = phrase_lower in content_lower
        if matched:
            events.append((category, f"фраза «{phrase}»", points))
    return events


def score_length(content: str) -> list[tuple[str, str, int]]:
    length = len(content)
    return [
        ("length", f"{threshold}+ символов", points)
        for threshold, points in LENGTH_TIERS
        if length >= threshold
    ]


def score_questions(content: str) -> list[tuple[str, str, int]]:
    count = content.count("?")
    events: list[tuple[str, str, int]] = []
    if count >= 1:
        events.append(("question", "в сообщении есть вопрос", 1))
    if count > 3:
        events.append(("question", f"{count} вопросов в сообщении", 5))
    if count > 7:
        events.append(("question", f"{count} вопросов в сообщении", 12))
    return events


def score_media(message) -> list[tuple[str, str, int]]:
    events: list[tuple[str, str, int]] = []
    if getattr(message, "photo", None):
        events.append(("media", "прислал скрин", 2))
    if getattr(message, "video", None):
        events.append(("media", "прислал видео", 4))
        caption = getattr(message, "caption", None) or ""
        if len(caption) >= LONG_CAPTION_THRESHOLD:
            events.append(("media", "видео с длинным описанием", 8))
    return events


def score_evening(local_dt: datetime) -> list[tuple[str, str, int]]:
    hour = local_dt.hour
    events: list[tuple[str, str, int]] = []
    if hour >= 20:
        events.append(("evening", "сообщение после 20:00", 2))
    if hour >= 22:
        events.append(("evening", "сообщение после 22:00", 5))
    if hour < 6:
        events.append(("evening", "сообщение после полуночи", 10))
    return events


def score_streak(count: int) -> tuple[str, str, int] | None:
    points = STREAK_TIERS.get(count)
    if points is None:
        return None
    return ("streak", f"{count} сообщений подряд", points)


# ── Time helpers ─────────────────────────────────────────────────────────────


def _now_msk() -> datetime:
    return datetime.now(UTC).astimezone(MOSCOW_TZ)


def _to_naive_utc(dt_aware: datetime) -> datetime:
    return dt_aware.astimezone(UTC).replace(tzinfo=None)


def _today_start_utc() -> datetime:
    return _to_naive_utc(
        datetime.combine(_now_msk().date(), time(0, 0), tzinfo=MOSCOW_TZ)
    )


def _week_start_utc() -> datetime:
    now_msk = _now_msk()
    monday = now_msk.date() - timedelta(days=now_msk.weekday())
    return _to_naive_utc(datetime.combine(monday, time(0, 0), tzinfo=MOSCOW_TZ))


# ── DB-touching functions ───────────────────────────────────────────────────


async def bump_streak(chat_id: int, user_id: int) -> int:
    """Обновляет счётчик подряд идущих сообщений одного пользователя в чате."""
    async with SessionLocal() as session:
        try:
            result = await session.execute(
                select(DushnilaStreak).filter(DushnilaStreak.chat_id == chat_id)
            )
            streak = result.scalars().first()
            if streak is None:
                streak = DushnilaStreak(chat_id=chat_id, user_id=user_id, count=1)
                session.add(streak)
            elif streak.user_id == user_id:
                streak.count += 1
            else:
                streak.user_id = user_id
                streak.count = 1
            await session.commit()
            return streak.count
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Ошибка обновления серии сообщений душнилы: %s", e)
            return 1


async def record_events(
    chat_id: int,
    user_id: int,
    full_name: str,
    username: str,
    message_id: int,
    events: list[tuple[str, str, int]],
) -> None:
    if not events:
        return
    async with SessionLocal() as session:
        try:
            for category, reason, points in events:
                session.add(
                    DushnilaEvent(
                        chat_id=chat_id,
                        user_id=user_id,
                        full_name=full_name,
                        username=username or "",
                        message_id=message_id,
                        category=category,
                        reason=reason,
                        points=points,
                    )
                )
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Ошибка записи баллов душнилы: %s", e)


async def score_dushnila_message(message) -> None:
    """Оценивает сообщение по критериям душности и сохраняет события в БД."""
    if not flags.DUSHNILA_ENABLE:
        return
    if not message.chat or message.chat.type == "private":
        return
    settings = get_settings()
    if message.chat.id not in settings.nfsw_chat_ids:
        return
    if not message.from_user:
        return

    content = message.text or message.caption or ""

    positive_phrases, negative_phrases = load_dushnila_phrases()

    events: list[tuple[str, str, int]] = []
    events += score_phrases(content, positive_phrases, "phrase")
    events += score_phrases(content, negative_phrases, "anti")
    events += score_length(content)
    events += score_questions(content)
    events += score_media(message)
    events += score_evening(_now_msk())

    streak_count = await bump_streak(message.chat.id, message.from_user.id)
    streak_event = score_streak(streak_count)
    if streak_event:
        events.append(streak_event)

    await record_events(
        message.chat.id,
        message.from_user.id,
        message.from_user.full_name,
        message.from_user.username or "",
        message.message_id,
        events,
    )


async def _totals_since(
    chat_id: int, since: datetime
) -> list[tuple[int, str, str, int]]:
    """Суммирует баллы по пользователям, используя имя/username, записанные
    непосредственно в DushnilaEvent на момент начисления (самые свежие —
    так как события отсортированы по created_at)."""
    async with SessionLocal() as session:
        result = await session.execute(
            select(DushnilaEvent)
            .filter(DushnilaEvent.chat_id == chat_id, DushnilaEvent.created_at >= since)
            .order_by(DushnilaEvent.created_at)
        )
        events = result.scalars().all()

    totals: dict[int, int] = {}
    identity: dict[int, tuple[str, str]] = {}
    for event in events:
        totals[event.user_id] = totals.get(event.user_id, 0) + event.points
        identity[event.user_id] = (event.full_name, event.username or "")

    rows = [
        (user_id, identity[user_id][0], identity[user_id][1], max(0, total))
        for user_id, total in totals.items()
    ]
    rows.sort(key=lambda row: row[3], reverse=True)
    return rows


async def get_week_start(chat_id: int) -> datetime:
    iso_start = _week_start_utc()
    async with SessionLocal() as session:
        result = await session.execute(
            select(DushnilaWeekReset).filter(DushnilaWeekReset.chat_id == chat_id)
        )
        reset = result.scalars().first()
    if reset and reset.reset_at > iso_start:
        return reset.reset_at
    return iso_start


async def get_weekly_totals(chat_id: int) -> list[tuple[int, str, str, int]]:
    return await _totals_since(chat_id, await get_week_start(chat_id))


async def get_today_totals(chat_id: int) -> list[tuple[int, str, str, int]]:
    return await _totals_since(chat_id, _today_start_utc())


async def get_personal_weekly_total(chat_id: int, user_id: int) -> int:
    week_start = await get_week_start(chat_id)
    async with SessionLocal() as session:
        result = await session.execute(
            select(func.sum(DushnilaEvent.points)).filter(
                DushnilaEvent.chat_id == chat_id,
                DushnilaEvent.user_id == user_id,
                DushnilaEvent.created_at >= week_start,
            )
        )
        total = result.scalar()
    return max(0, int(total or 0))


async def get_today_events(
    chat_id: int, user_id: int, limit: int = 10
) -> list[DushnilaEvent]:
    async with SessionLocal() as session:
        result = await session.execute(
            select(DushnilaEvent)
            .filter(
                DushnilaEvent.chat_id == chat_id,
                DushnilaEvent.user_id == user_id,
                DushnilaEvent.created_at >= _today_start_utc(),
            )
            .order_by(DushnilaEvent.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


async def find_participant_by_username(
    chat_id: int, username: str
) -> Participant | None:
    normalized = username.lstrip("@").strip().lower()
    if not normalized:
        return None
    async with SessionLocal() as session:
        result = await session.execute(
            select(Participant).filter(
                Participant.chat_id == chat_id,
                func.lower(Participant.username) == normalized,
            )
        )
        return result.scalars().first()


async def reset_week(chat_id: int) -> None:
    now = datetime.now(UTC).replace(tzinfo=None)
    async with SessionLocal() as session:
        try:
            result = await session.execute(
                select(DushnilaWeekReset).filter(DushnilaWeekReset.chat_id == chat_id)
            )
            reset = result.scalars().first()
            if reset is None:
                session.add(DushnilaWeekReset(chat_id=chat_id, reset_at=now))
            else:
                reset.reset_at = now
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Ошибка сброса недельного рейтинга душнилы: %s", e)
