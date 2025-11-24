import asyncio
import logging
import os
import random
from datetime import UTC, datetime, time, timedelta, timezone

from aiogram import Bot
from aiogram.types import FSInputFile
from sqlalchemy import delete, select, update

from bot.config import flags
from bot.config.tokens import GOOD_MORNING_CHAT_ID
from bot.database import SessionLocal
from bot.models import MorningImage


IMAGES_DIR = os.path.join(os.path.dirname(__file__), "morning_pic")

# Часовой пояс UTC+3 (например, Москва)
MOSCOW_TZ = timezone(timedelta(hours=3))


async def _sync_db_with_files(session, files: list[str]) -> None:
    """Добавляет новые файлы в таблицу и удаляет те, которых больше нет."""
    result = await session.execute(select(MorningImage))
    existing = result.scalars().all()
    existing_names = {row.filename for row in existing}
    changed = False

    for filename in files:
        if filename not in existing_names:
            session.add(MorningImage(filename=filename, used=False))
            changed = True

    removed = [row.filename for row in existing if row.filename not in files]
    if removed:
        await session.execute(
            delete(MorningImage).where(MorningImage.filename.in_(removed))
        )
        changed = True

    if changed:
        await session.commit()


async def _select_available_images(session) -> list[MorningImage]:
    """Возвращает список ещё не отправленных картинок."""
    result = await session.execute(
        select(MorningImage).where(MorningImage.used.is_(False))
    )
    available = result.scalars().all()
    if available:
        return available

    await session.execute(update(MorningImage).values(used=False))
    await session.commit()
    result = await session.execute(
        select(MorningImage).where(MorningImage.used.is_(False))
    )
    return result.scalars().all()


async def _reserve_image() -> tuple[str, int, str] | None:
    """
    Возвращает путь и идентификатор случайной картинки и помечает её как «использованную».
    """
    if not os.path.isdir(IMAGES_DIR):
        logging.warning(
            "Папка с картинками для доброго утра не найдена: %s", IMAGES_DIR
        )
        return None

    allowed_ext = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    files = [
        f
        for f in os.listdir(IMAGES_DIR)
        if os.path.isfile(os.path.join(IMAGES_DIR, f))
        and os.path.splitext(f)[1].lower() in allowed_ext
    ]

    if not files:
        logging.warning(
            "В папке %s не найдено ни одной подходящей картинки для доброго утра",
            IMAGES_DIR,
        )
        return None

    async with SessionLocal() as session:
        await _sync_db_with_files(session, files)
        available = await _select_available_images(session)
        if not available:
            logging.warning("Не удалось подобрать картинку: таблица пуста")
            return None

        record = random.choice(available)
        record.used = True
        await session.commit()
        return os.path.join(IMAGES_DIR, record.filename), record.id, record.filename


async def _finalize_image_usage(image_id: int, success: bool) -> None:
    """Фиксирует результат отправки картинки."""
    async with SessionLocal() as session:
        image = await session.get(MorningImage, image_id)
        if not image:
            return
        if success:
            image.last_sent_at = datetime.now(UTC)
        else:
            image.used = False
            image.last_sent_at = None
        await session.commit()


async def send_good_morning(bot: Bot) -> bool:
    """
    Отправляет сообщение «Доброе утро» и случайную картинку в указанный чат.

    Чат берётся из переменной окружения GOOD_MORNING_CHAT_ID.
    Если чат или картинка не найдены, только логируем предупреждение.
    """
    if not flags.GOOD_MORNING_ENABLE:
        logging.info(
            "GOOD_MORNING_ENABLE=False, утреннее сообщение отправляться "
            "не будет",
        )
        return False
    if not GOOD_MORNING_CHAT_ID:
        logging.info(
            "GOOD_MORNING_CHAT_ID не задан, утреннее сообщение отправляться "
            "не будет",
        )
        return False

    image_info = await _reserve_image()
    if image_info is None:
        # уже залогировано внутри _get_random_image_path
        return False
    image_path, image_id, filename = image_info

    try:
        photo = FSInputFile(image_path)
        await bot.send_photo(
            chat_id=GOOD_MORNING_CHAT_ID,
            photo=photo,
            caption="Доброе утро",
        )
        logging.info(
            "Утреннее сообщение успешно отправлено в чат %s с картинкой %s",
            GOOD_MORNING_CHAT_ID,
            image_path,
        )
        await _finalize_image_usage(image_id, success=True)
        return True
    except Exception as exc:  # noqa: BLE001
        logging.exception("Ошибка при отправке утреннего сообщения: %s", exc)
        await _finalize_image_usage(image_id, success=False)
        return False


async def schedule_good_morning(bot: Bot,
                                hour: int = 9,
                                minute: int = 00) -> None:
    """
    Периодически отправляет утреннее сообщение по будням.

    По умолчанию в 09:00 по времени UTC+3 (MOSCOW_TZ), независимо от
    часового пояса сервера.
    """
    while True:
        if not flags.GOOD_MORNING_ENABLE:
            logging.info(
                "GOOD_MORNING_ENABLE=False, планировщик доброго утра остановлен",
            )
            return
        # Текущее время в UTC и в часовом поясе UTC+3
        now_utc = datetime.now(UTC)
        now_local = now_utc.astimezone(MOSCOW_TZ)

        # Целевое время сегодня в UTC+3
        target_today_local = datetime.combine(
            now_local.date(),
            time(hour=hour, minute=minute, tzinfo=MOSCOW_TZ),
        )

        # Если уже позже целевого времени — переносим на следующий день
        if now_local >= target_today_local:
            next_run_local = target_today_local + timedelta(days=1)
        else:
            next_run_local = target_today_local

        # Пропускаем выходные: weekday() 0-4 – будни, 5-6 – выходные
        while next_run_local.weekday() >= 5:
            next_run_local += timedelta(days=1)

        # Переводим момент запуска в UTC и считаем задержку
        next_run_utc = next_run_local.astimezone(UTC)
        sleep_seconds = (next_run_utc - now_utc).total_seconds()

        logging.info(
            "Следующее утреннее сообщение будет отправлено %s (локально %s) "
            "(через %.0f секунд)",
            next_run_utc,
            next_run_local,
            sleep_seconds,
        )

        await asyncio.sleep(max(sleep_seconds, 0))
        await send_good_morning(bot)
