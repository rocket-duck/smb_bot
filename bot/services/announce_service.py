import logging
from typing import Dict, Any, List
from bot.database import SessionLocal
from bot.models import Chat

logger = logging.getLogger(__name__)

def get_active_chats() -> List[Dict[str, Any]]:
    session = SessionLocal()
    try:
        rows = session.query(Chat).filter(Chat.deleted.is_(False)).all()
        return [{"id": c.chat_id, "title": c.title} for c in rows]
    finally:
        session.close()