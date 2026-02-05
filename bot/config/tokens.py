from bot.config.settings import get_settings

_settings = get_settings()

# Telegram Bot tokens
BOT_USERNAME = _settings.bot_username
API_TOKEN = _settings.api_token

# OpenAI token
OPENAI_API_KEY = _settings.openai_api_key

# Чаты для отправки NSFW-картинок
NFSW_CHAT_ID = _settings.nfsw_chat_ids
