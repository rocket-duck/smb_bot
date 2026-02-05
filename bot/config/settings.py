from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from functools import lru_cache

DEFAULT_DATABASE_URL = "sqlite+aiosqlite:///data/bot.db"


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise RuntimeError(f"{name} is not set")
    return value


def _parse_chat_ids(value: str | None) -> list[int]:
    if not value:
        return []
    raw = value.strip()
    if not raw:
        return []
    if raw.startswith("["):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [int(item) for item in parsed]
            return [int(parsed)]
        except (ValueError, TypeError, json.JSONDecodeError):
            pass
    parts = [part for part in re.split(r"[,\s]+", raw) if part]
    return [int(part) for part in parts]


def _parse_log_level(value: str | None) -> int:
    if not value:
        return logging.INFO
    if value.isdigit():
        return int(value)
    return logging._nameToLevel.get(value.upper(), logging.INFO)


def _parse_float(value: str | None, default: float) -> float:
    if value is None or value == "":
        return default
    return float(value)


@dataclass(frozen=True)
class Settings:
    bot_username: str
    api_token: str
    openai_api_key: str
    nfsw_chat_ids: list[int]
    database_url: str
    log_level: int
    sentry_dsn: str | None
    sentry_environment: str
    sentry_traces_sample_rate: float
    sentry_profiles_sample_rate: float
    sentry_release: str | None


@lru_cache
def get_settings() -> Settings:
    return Settings(
        bot_username=_require_env("BOT_USERNAME"),
        api_token=_require_env("API_TOKEN"),
        openai_api_key=_require_env("OPENAI_API_KEY"),
        nfsw_chat_ids=_parse_chat_ids(os.getenv("NFSW_CHAT_ID")),
        database_url=os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
        log_level=_parse_log_level(os.getenv("LOG_LEVEL")),
        sentry_dsn=os.getenv("SENTRY_DSN"),
        sentry_environment=os.getenv("SENTRY_ENVIRONMENT", "development"),
        sentry_traces_sample_rate=_parse_float(
            os.getenv("SENTRY_TRACES_SAMPLE_RATE"), 0.0
        ),
        sentry_profiles_sample_rate=_parse_float(
            os.getenv("SENTRY_PROFILES_SAMPLE_RATE"), 0.0
        ),
        sentry_release=os.getenv("SENTRY_RELEASE"),
    )
