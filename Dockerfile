FROM python:3.13.3-slim AS builder

# Задаём рабочую директорию внутри контейнера
WORKDIR /app

# Копируем основные файлы проекта
COPY pyproject.toml poetry.lock README.md Makefile ./
# Копируем каталог с исходниками
COPY bot/ ./bot/

RUN apt-get update && apt-get install -y \
      make \
      curl \
      build-essential \
      python3-dev \
    && pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && PIP_NO_CACHE_DIR=1 poetry install --no-interaction --no-ansi \
    && apt-get purge -y build-essential python3-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* /root/.cache/pypoetry /root/.cache/pip

# Копируем оставшиеся файлы проекта (если они есть)
COPY . .

FROM python:3.13.3-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends make && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.13 /usr/local/lib/python3.13
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

RUN mkdir -p /root/smb_bot/data && mkdir -p /root/smb_bot/logs

CMD ["make", "bot-run"]
