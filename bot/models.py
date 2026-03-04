from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String, UniqueConstraint, func

from bot.database import Base


class LastWinner(Base):
    __tablename__ = "last_winner"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(BigInteger, unique=True, index=True, nullable=False)
    chat_title = Column(String, nullable=True)
    last_datetime = Column(DateTime, default=func.now(), nullable=False)
    winner_user_id = Column(BigInteger, nullable=False)
    winner_full_name = Column(String, nullable=False)
    winner_username = Column(String, nullable=True)


class WinnerStats(Base):
    __tablename__ = "winner_stats"
    __table_args__ = (UniqueConstraint("chat_id", "user_id", name="uq_winner_stats_chat_user"),)

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(BigInteger, index=True, nullable=False)
    chat_title = Column(String, nullable=True)
    user_id = Column(BigInteger, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    username = Column(String, nullable=True)
    wins = Column(Integer, default=0, nullable=False)


class Participant(Base):
    __tablename__ = "participants"
    __table_args__ = (UniqueConstraint("chat_id", "user_id", name="uq_participants_chat_user"),)

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(BigInteger, index=True, nullable=False)
    user_id = Column(BigInteger, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    username = Column(String, nullable=True)
    chat_title = Column(String, nullable=True)
    last_active = Column(DateTime, nullable=True, index=True)


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(BigInteger, unique=True, nullable=False, index=True)
    title = Column(String, nullable=True)
    added_by = Column(String, nullable=True)
    added_at = Column(DateTime, default=func.now(), nullable=False)
    deleted = Column(Boolean, default=False)
    deleted_by = Column(String, nullable=True)
    deleted_at = Column(DateTime, nullable=True)


class SearchLog(Base):
    __tablename__ = "search_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=False)
    query = Column(String, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)


class MorningImage(Base):
    __tablename__ = "morning_images"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    last_sent_at = Column(DateTime, nullable=True)
