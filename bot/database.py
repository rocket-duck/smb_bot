from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# Здесь мы используем SQLite и сохраняем базу в файле data/bot.db
DATABASE_URL = "sqlite:///data/bot.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    # Импортируем модели, чтобы они были зарегистрированы в Base.metadata
    Base.metadata.create_all(bind=engine)
