from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from bot.config.settings import get_settings

settings = get_settings()

# Здесь мы используем SQLite и сохраняем базу в файле data/bot.db
DATABASE_URL = settings.database_url

engine: AsyncEngine = create_async_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()


async def init_db():
    # Импортируем модели, чтобы они были зарегистрированы в Base.metadata
    from bot import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
