import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# Telegram Bot tokens
BOT_USERNAME = os.getenv("BOT_USERNAME")
if BOT_USERNAME is None:
    raise RuntimeError("BOT_USERNAME is not set")

API_TOKEN = os.getenv("API_TOKEN")
if API_TOKEN is None:
    raise RuntimeError("API_TOKEN is not set")

# OpenAI token
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY is None:
    raise RuntimeError("OPENAI_API_KEY is not set")

# пользователь который выдает доступ к админ правам
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")
