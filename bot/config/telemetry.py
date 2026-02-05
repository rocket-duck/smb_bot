from __future__ import annotations

import logging

from bot.config.settings import Settings


def setup_sentry(settings: Settings) -> None:
    if not settings.sentry_dsn:
        logging.debug("Sentry DSN не задан, инициализация пропущена.")
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration
    except Exception as exc:  # noqa: BLE001
        logging.warning("Sentry SDK не установлен: %s", exc)
        return

    sentry_logging = LoggingIntegration(
        level=logging.ERROR,
        event_level=logging.ERROR,
    )

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        release=settings.sentry_release,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        profiles_sample_rate=settings.sentry_profiles_sample_rate,
        send_default_pii=False,
        integrations=[sentry_logging],
    )
    logging.info("Sentry инициализирован.")
