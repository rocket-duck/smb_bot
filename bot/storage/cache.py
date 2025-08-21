import os
import sqlite3
import threading
from datetime import datetime


class SQLiteCache:
    """Simple SQLite-backed cache with TTL support."""

    def __init__(self, path: str = "data/cache.db"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS recent_links (
                chat_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                expires_at REAL NOT NULL,
                PRIMARY KEY (chat_id, url)
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reaction_counts (
                chat_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                likes INTEGER NOT NULL DEFAULT 0,
                dislikes INTEGER NOT NULL DEFAULT 0,
                expires_at REAL NOT NULL,
                PRIMARY KEY (chat_id, message_id)
            )
            """
        )
        self.conn.commit()
        self.lock = threading.Lock()

    # --- Recent links operations ---
    def set_recent_link(self, chat_id: int, url: str, ttl_seconds: int) -> None:
        with self.lock:
            expires_at = datetime.now().timestamp() + ttl_seconds
            self.conn.execute(
                "REPLACE INTO recent_links(chat_id, url, expires_at) VALUES(?,?,?)",
                (chat_id, url, expires_at),
            )
            self.conn.commit()

    def is_recent_link(self, chat_id: int, url: str) -> bool:
        with self.lock:
            now = datetime.now().timestamp()
            cur = self.conn.execute(
                "SELECT expires_at FROM recent_links WHERE chat_id=? AND url=?",
                (chat_id, url),
            )
            row = cur.fetchone()
            if not row:
                return False
            if row[0] < now:
                self.conn.execute(
                    "DELETE FROM recent_links WHERE chat_id=? AND url=?",
                    (chat_id, url),
                )
                self.conn.commit()
                return False
            return True

    # --- Reaction counts operations ---
    def init_reaction(self, chat_id: int, message_id: int, ttl_seconds: int) -> None:
        with self.lock:
            expires_at = datetime.now().timestamp() + ttl_seconds
            self.conn.execute(
                "REPLACE INTO reaction_counts(chat_id, message_id, likes, dislikes, expires_at) VALUES(?,?,?,?,?)",
                (chat_id, message_id, 0, 0, expires_at),
            )
            self.conn.commit()

    def increment_reaction(self, chat_id: int, message_id: int, reaction: str, ttl_seconds: int):
        with self.lock:
            now = datetime.now().timestamp()
            expires_at = now + ttl_seconds
            cur = self.conn.execute(
                "SELECT likes, dislikes, expires_at FROM reaction_counts WHERE chat_id=? AND message_id=?",
                (chat_id, message_id),
            )
            row = cur.fetchone()
            if not row or row[2] < now:
                likes = dislikes = 0
            else:
                likes, dislikes, _ = row
            if reaction == "like":
                likes += 1
            else:
                dislikes += 1
            self.conn.execute(
                "REPLACE INTO reaction_counts(chat_id, message_id, likes, dislikes, expires_at) VALUES(?,?,?,?,?)",
                (chat_id, message_id, likes, dislikes, expires_at),
            )
            self.conn.commit()
            return likes, dislikes

    def get_reaction(self, chat_id: int, message_id: int):
        with self.lock:
            now = datetime.now().timestamp()
            cur = self.conn.execute(
                "SELECT likes, dislikes, expires_at FROM reaction_counts WHERE chat_id=? AND message_id=?",
                (chat_id, message_id),
            )
            row = cur.fetchone()
            if not row:
                return None
            likes, dislikes, expires_at = row
            if expires_at < now:
                self.conn.execute(
                    "DELETE FROM reaction_counts WHERE chat_id=? AND message_id=?",
                    (chat_id, message_id),
                )
                self.conn.commit()
                return None
            return {"likes": likes, "dislikes": dislikes}

    def remove_reaction(self, chat_id: int, message_id: int) -> None:
        with self.lock:
            self.conn.execute(
                "DELETE FROM reaction_counts WHERE chat_id=? AND message_id=?",
                (chat_id, message_id),
            )
            self.conn.commit()


cache = SQLiteCache()
