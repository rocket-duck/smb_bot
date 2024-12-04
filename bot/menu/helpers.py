import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

def is_valid_url(url):
    """
    Проверяет, является ли строка валидным URL.
    """
    return isinstance(url, str) and url.startswith(("http://", "https://"))
