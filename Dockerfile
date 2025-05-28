FROM python:3.13.3-slim

WORKDIR /app

# Install make, curl and Poetry
RUN apt-get update && apt-get install -y --no-install-recommends \
      make \
      curl \
      build-essential \
      python3-dev \
    && pip install --no-cache-dir poetry \
    && rm -rf /var/lib/apt/lists/*

# Copy all project files
COPY . .

CMD ["sh", "-c", "poetry install --no-interaction --no-ansi --no-root > /dev/null 2>&1 && exec poetry run python3 -m bot.main"]