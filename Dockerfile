FROM python:3.13.3-slim

# Устанавливаем необходимые утилиты и Poetry
RUN apt-get update && apt-get install -y make curl && \
    pip install --no-cache-dir poetry

# Задаём рабочую директорию внутри контейнера
WORKDIR /app

# Создаём директории для данных и логов, которые будут примонтированы
RUN mkdir -p /root/smb_bot/data && mkdir -p /root/smb_bot/logs

# Копируем основные файлы проекта
COPY pyproject.toml poetry.lock README.md Makefile ./
# Копируем каталог с исходниками
COPY bot/ ./bot/

# Выполняем установку зависимостей через Makefile (Makefile должен использовать "poetry install")
RUN make install

# Копируем оставшиеся файлы проекта (если они есть)
COPY . .

# Определяем команду для запуска бота через Makefile
CMD ["make", "bot-run"]
