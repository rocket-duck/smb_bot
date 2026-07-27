import asyncio
import logging
from datetime import UTC, datetime, time, timedelta

from aiogram import Bot

from bot.commands.best_qa import run_best_qa
from bot.config import flags
from bot.config.flags import BEST_QA_DIGEST_HOUR, BEST_QA_DIGEST_MINUTE
from bot.config.settings import get_settings
from bot.utils.good_morning import MOSCOW_TZ


async def _resolve_chat_title(bot: Bot, chat_id: int) -> str:
    try:
        chat = await bot.get_chat(chat_id)
        return chat.title or str(chat_id)
    except Exception as exc:  # noqa: BLE001
        logging.warning("Не удалось получить название чата %s: %s", chat_id, exc)
        return str(chat_id)


async def run_daily_best_qa(bot: Bot) -> None:
    """Запускает выбор лучшего тестировщика дня во всех настроенных чатах."""
    if not flags.BEST_QA_ENABLE:
        logging.info("BEST_QA_ENABLE=False, ежедневный запуск best_qa пропущен")
        return

    settings = get_settings()
    if not settings.nfsw_chat_ids:
        logging.info("NFSW_CHAT_ID не задан, ежедневный запуск best_qa пропущен")
        return

    for chat_id in settings.nfsw_chat_ids:
        chat_title = await _resolve_chat_title(bot, chat_id)
        try:
            await run_best_qa(bot, chat_id, chat_title)
        except Exception as exc:  # noqa: BLE001
            logging.exception(
                "Ошибка при автоматическом запуске best_qa в чате %s: %s", chat_id, exc
            )


async def schedule_best_qa_digest(
    bot: Bot, hour: int = BEST_QA_DIGEST_HOUR, minute: int = BEST_QA_DIGEST_MINUTE
) -> None:
    """
    Периодически запускает выбор лучшего тестировщика дня по будням.

    По умолчанию в 18:00 по времени UTC+3 (MOSCOW_TZ), независимо от
    часового пояса сервера. Выходные (сб/вс) пропускаются.
    """
    while True:
        if not flags.BEST_QA_ENABLE:
            logging.info("BEST_QA_ENABLE=False, планировщик best_qa остановлен")
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
            "Следующий автоматический запуск best_qa будет в %s (локально %s) "
            "(через %.0f секунд)",
            next_run_utc,
            next_run_local,
            sleep_seconds,
        )

        await asyncio.sleep(max(sleep_seconds, 0))
        await run_daily_best_qa(bot)
