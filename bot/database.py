from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base


# Здесь мы используем SQLite и сохраняем базу в файле data/bot.db
DATABASE_URL = "sqlite+aiosqlite:///data/bot.db"

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

        # Simple manual migration for existing databases without new columns.
        result = await conn.execute(text("PRAGMA table_info(participants)"))
        columns = [row[1] for row in result]
        if "last_active" not in columns:
            await conn.execute(
                text("ALTER TABLE participants ADD COLUMN last_active DATETIME")
            )
