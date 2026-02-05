# SMB Bot

Telegram-бот для команды SMB: справочные ссылки, игровые/фановые команды, поиск по OpenAI и утренние сообщения с картинками.

## Быстрый старт

### Локально (Poetry)
```
poetry install
poetry run bot
```

### Docker
```
docker compose up --build
```

## Переменные окружения

Минимальный набор:
- `BOT_USERNAME` — username бота без `@`
- `API_TOKEN` — токен Telegram бота
- `OPENAI_API_KEY` — ключ OpenAI

Дополнительно:
- `NFSW_CHAT_ID` — список чатов для отправки NSFW-картинок. Форматы:
  - `-123456789`
  - `-123456789,-987654321`
  - `[-123456789,-987654321]`
- `DATABASE_URL` — строка подключения БД (по умолчанию `sqlite+aiosqlite:///data/bot.db`)
- `LOG_LEVEL` — уровень логов (`INFO`, `WARNING`, `ERROR` и т.д.)
- `SENTRY_DSN` — DSN Sentry (если не задан, Sentry не инициализируется)
- `SENTRY_ENVIRONMENT` — окружение Sentry (по умолчанию `development`)
- `SENTRY_TRACES_SAMPLE_RATE` — доля трейсинга (0.0 по умолчанию)
- `SENTRY_PROFILES_SAMPLE_RATE` — доля профайлинга (0.0 по умолчанию)
- `SENTRY_RELEASE` — версия релиза для Sentry

Используется основной `docker-compose.yml`.
Переменные задаются через `environment` и подставляются из окружения хоста.
Пример запуска:

```
export BOT_USERNAME="smb_mbbiz_bot"
export API_TOKEN="***"
export OPENAI_API_KEY="***"
export NFSW_CHAT_ID="-1001783443049"
docker compose up -d
```

## Команды бота

Актуальный список команд можно получить через `/help`.  
Команды включаются/выключаются через флаги в `bot/config/flags.py`.

## Утренние сообщения

- Планировщик живёт в `bot/utils/good_morning.py`
- Отправка по будням в 09:00 (UTC+3)
- Картинки берутся из `bot/utils/morning_pic`
- Фразы — из `bot/dicts/good_morning_phrases.json` (можно дополнять вручную)
- Отправка идёт только в чаты из `NFSW_CHAT_ID`

## Контент-слой

Для валидации контента используется `bot/content/good_morning_content.py`:
- проверяет наличие и формат JSON с фразами
- фильтрует картинки по расширению

## Миграции (Alembic)

Инициализация (один раз):
```
poetry run alembic upgrade head
```

Новая миграция:
```
poetry run alembic revision -m "описание"
```

## Проверки качества

Линтер:
```
poetry run ruff check bot tests
```

Форматтер:
```
poetry run black bot tests
```

Makefile:
```
make lint
make format
```

## Тесты

```
poetry run pytest
```

## Запуск в проде

Бот запускается через `bot/utils/run_bot.py`.  
Инициализация логов и Sentry производится при старте.

## Публикация Docker образа (GHCR)

В репозитории есть workflow `.github/workflows/docker-publish.yml`, который
собирает и публикует образ в GHCR при пуше в `main`.

Тэги:
- `ghcr.io/<owner>/<repo>:latest`
- `ghcr.io/<owner>/<repo>:<commit_sha>`
