FROM python:3.13.3-slim

# Задаём рабочую директорию внутри контейнера
WORKDIR /app

# Создаём директории для данных и логов, которые будут примонтированы
RUN mkdir -p /root/smb_bot/data && mkdir -p /root/smb_bot/logs

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
    && PIP_NO_CACHE_DIR=1 poetry install --no-interaction --no-ansi --without dev \
    && apt-get purge -y build-essential python3-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* /root/.cache/pypoetry /root/.cache/pip

# Копируем оставшиеся файлы проекта (если они есть)
COPY . .

# Определяем команду для запуска бота через Makefile
CMD ["make", "bot-run"]
