import pytest
from types import SimpleNamespace

import bot.services.best_qa_stat_service as service

class DummyQuery:
    def __init__(self, results=None, raise_exc=False):
        self._results = results or []
        self._raise = raise_exc

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def all(self):
        if self._raise:
            raise RuntimeError("DB error")
        return self._results

class DummySession:
    def __init__(self, query_obj):
        self._query_obj = query_obj
        self.closed = False

    def query(self, model):
        return self._query_obj

    def close(self):
        self.closed = True

class DummySessionLocal:
    """Фабрика сессий. При создании принимает DummyQuery."""
    def __init__(self, query_obj):
        self._query_obj = query_obj
        self.sessions_created = []

    def __call__(self):
        s = DummySession(self._query_obj)
        self.sessions_created.append(s)
        return s

class DummyStat:
    def __init__(self, chat_id, chat_title, full_name, username, wins):
        self.chat_id = chat_id
        self.chat_title = chat_title
        self.full_name = full_name
        self.username = username
        self.wins = wins

@pytest.fixture(autouse=True)
def suppress_logging(monkeypatch):
    # Чтобы не засорять тесты логами
    monkeypatch.setattr(service, "logger", SimpleNamespace(info=lambda *a, **k: None,
                                                          warning=lambda *a, **k: None,
                                                          error=lambda *a, **k: None))

def test_get_stats_success(monkeypatch):
    # Подготовим два DummyStat
    stats_list = [
        DummyStat("c1", "Chat1", "Alice", "alice", 3),
        DummyStat("c1", "Chat1", "Bob", "bob", 1),
    ]
    dq = DummyQuery(results=stats_list)
    # Перехватим фабрику сессий
    monkeypatch.setattr(service, "SessionLocal", DummySessionLocal(dq))
    # *** правильный способ вызвать ***
    import asyncio
    stats = asyncio.get_event_loop().run_until_complete(service.get_stats("c1"))

    assert stats == stats_list
    # Сессия из get_stats должна быть закрыта
    session_local = service.SessionLocal
    assert hasattr(session_local, "sessions_created")
    assert len(session_local.sessions_created) == 1
    session = session_local.sessions_created[0]
    assert session.closed

def test_get_stats_db_error(monkeypatch):
    dq = DummyQuery(raise_exc=True)
    monkeypatch.setattr(service, "SessionLocal", DummySessionLocal(dq))
    import asyncio
    with pytest.raises(service.StatsServiceError):
        asyncio.get_event_loop().run_until_complete(service.get_stats("cX"))

def test_format_stats_text_empty():
    # Пустой список, пустой заголовок -> "Чат"
    text = service.format_stats_text([], "")
    assert "Чат:" in text or "Чат" in text

def test_format_stats_text_with_data(monkeypatch):
    # Подменим склонение, чтобы тест был предсказуем
    monkeypatch.setattr(service, "format_declension", lambda n: "раз(а)")
    stats = [
        DummyStat("c2", "MyChat", "Carol", None, 5),
        DummyStat("c2", "MyChat", "Dave", "dave", 1),
    ]
    # Заголовок из параметра
    text = service.format_stats_text(stats, "CustomTitle")
    assert "CustomTitle" in text
    assert "Carol: 5 раз(а)" in text
    assert "Dave (@dave): 1 раз(а)" in text
    # Проверим, что каждая строка начинается с •
    lines = text.splitlines()
    assert lines[1].startswith("• ")
