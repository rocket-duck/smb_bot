from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from bot.database import Base


class LastWinner(Base):
    __tablename__ = "last_winner"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, unique=True, index=True, nullable=False)
    chat_title = Column(String, nullable=True)
    last_datetime = Column(DateTime, default=func.now(), nullable=False)
    winner_user_id = Column(String, nullable=False)
    winner_full_name = Column(String, nullable=False)
    winner_username = Column(String, nullable=True)


class WinnerStats(Base):
    __tablename__ = "winner_stats"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, index=True, nullable=False)
    chat_title = Column(String, nullable=True)
    user_id = Column(String, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    username = Column(String, nullable=True)
    wins = Column(Integer, default=0, nullable=False)


class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, index=True, nullable=False)
    user_id = Column(String, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    username = Column(String, nullable=True)
    chat_title = Column(String, nullable=True)


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=True)
    added_by = Column(String, nullable=True)
    added_at = Column(DateTime, default=func.now(), nullable=False)
    deleted = Column(Boolean, default=False)
    deleted_by = Column(String, nullable=True)
    deleted_at = Column(DateTime, nullable=True)


class SearchLog(Base):
    __tablename__ = "search_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=False)
    query = Column(String, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, nullable=False)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=False)
    added_at = Column(DateTime, default=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    removed_at = Column(DateTime, nullable=True)
