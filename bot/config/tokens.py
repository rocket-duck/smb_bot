import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# Telegram Bot tokens
BOT_USERNAME = os.getenv("BOT_USERNAME")
API_TOKEN = os.getenv("API_TOKEN")

# OpenAI token
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# пользователь который выдает доступ к админ правам
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")
