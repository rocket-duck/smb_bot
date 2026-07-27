import asyncio
import logging
from datetime import UTC, datetime, time, timedelta

from aiogram import Bot

from bot.config import flags
from bot.config.flags import DUSHNILA_DIGEST_HOUR, DUSHNILA_DIGEST_MINUTE
from bot.config.settings import get_settings
from bot.utils.dushnila_engine import (
    format_points_declension,
    get_today_totals,
    level_for_score,
)
from bot.utils.good_morning import MOSCOW_TZ


def format_digest(totals: list[tuple[int, str, str, int]]) -> str:
    """Форматирует итоги дня по душности."""
    lines = ["📊 Итоги дня по душности"]
    for rank, (_, full_name, _, total) in enumerate(totals, start=1):
        declension = format_points_declension(total)
        level = level_for_score(total)
        lines.append(f"{rank}. {full_name} — {total} {declension} {level}")
    return "\n".join(lines)


async def send_dushnila_digest(bot: Bot) -> bool:
    """Отправляет итоги дня по душности во все настроенные чаты."""
    if not flags.DUSHNILA_ENABLE:
        logging.info("DUSHNILA_ENABLE=False, итоги дня отправляться не будут")
        return False

    settings = get_settings()
    if not settings.nfsw_chat_ids:
        logging.info("NFSW_CHAT_ID не задан, итоги дня отправляться не будут")
        return False

    sent_any = False
    for chat_id in settings.nfsw_chat_ids:
        totals = await get_today_totals(chat_id)
        if not totals:
            logging.debug("Нет активности душнил за сегодня в чате %s", chat_id)
            continue
        try:
            await bot.send_message(chat_id=chat_id, text=format_digest(totals))
            sent_any = True
        except Exception as exc:  # noqa: BLE001
            logging.exception(
                "Ошибка при отправке итогов дня душнилы в чат %s: %s", chat_id, exc
            )

    return sent_any


async def schedule_dushnila_digest(
    bot: Bot, hour: int = DUSHNILA_DIGEST_HOUR, minute: int = DUSHNILA_DIGEST_MINUTE
) -> None:
    """
    Периодически отправляет итоги дня по душности по будням.

    По умолчанию в 18:00 по времени UTC+3 (MOSCOW_TZ), независимо от
    часового пояса сервера. Выходные (сб/вс) пропускаются.
    """
    while True:
        if not flags.DUSHNILA_ENABLE:
            logging.info("DUSHNILA_ENABLE=False, планировщик итогов дня остановлен")
            return

        now_utc = datetime.now(UTC)
        now_local = now_utc.astimezone(MOSCOW_TZ)

        target_today_local = datetime.combine(
            now_local.date(),
            time(hour=hour, minute=minute, tzinfo=MOSCOW_TZ),
        )

        if now_local >= target_today_local:
            next_run_local = target_today_local + timedelta(days=1)
        else:
            next_run_local = target_today_local

        # Пропускаем выходные: weekday() 0-4 – будни, 5-6 – выходные
        while next_run_local.weekday() >= 5:
            next_run_local += timedelta(days=1)

        next_run_utc = next_run_local.astimezone(UTC)
        sleep_seconds = (next_run_utc - now_utc).total_seconds()

        logging.info(
            "Следующие итоги дня душнилы будут отправлены %s (локально %s) "
            "(через %.0f секунд)",
            next_run_utc,
            next_run_local,
            sleep_seconds,
        )

        await asyncio.sleep(max(sleep_seconds, 0))
        await send_dushnila_digest(bot)
