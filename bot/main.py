import asyncio

from dotenv import load_dotenv

# Загружаем переменные окружения до импорта остальных модулей
load_dotenv()

from bot.utils.run_bot import run_bot  # noqa: E402


def main():
    asyncio.run(run_bot())


if __name__ == "__main__":
    asyncio.run(run_bot())
