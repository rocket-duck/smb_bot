FROM python:3.13.3-slim

# Устанавливаем необходимые утилиты и Poetry
RUN apt-get update && apt-get install -y \
      make \
      curl \
      build-essential \
      python3-dev \
    && pip install --no-cache-dir poetry \
    && rm -rf /var/lib/apt/lists/*

# Задаём рабочую директорию внутри контейнера
WORKDIR /app

# Создаём директории для данных и логов, которые будут примонтированы
RUN mkdir -p /root/smb_bot/data && mkdir -p /root/smb_bot/logs

# Копируем основные файлы проекта
COPY pyproject.toml poetry.lock README.md Makefile ./
# Копируем каталог с исходниками
COPY bot/ ./bot/

# Install production dependencies without dev packages and clear cache to save space
RUN poetry install --no-dev --no-interaction --no-ansi \
    && rm -rf /root/.cache/pypoetry \
    && rm -rf /root/.cache/pip

# Копируем оставшиеся файлы проекта (если они есть)
COPY . .

# Определяем команду для запуска бота через Makefile
CMD ["make", "bot-run"]
