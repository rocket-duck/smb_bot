import time
from bot.storage.cache import SQLiteCache


def test_recent_link_expiration(tmp_path):
    cache = SQLiteCache(str(tmp_path / 'cache.db'))
    cache.set_recent_link(123, 'http://example.com', ttl_seconds=1)
    assert cache.is_recent_link(123, 'http://example.com') is True
    time.sleep(1.1)
    assert cache.is_recent_link(123, 'http://example.com') is False
    cache.conn.close()


def test_reaction_counts(tmp_path):
    cache = SQLiteCache(str(tmp_path / 'cache.db'))
    cache.init_reaction(1, 42, ttl_seconds=1)
    assert cache.get_reaction(1, 42) == {'likes': 0, 'dislikes': 0}

    likes, dislikes = cache.increment_reaction(1, 42, 'like', ttl_seconds=1)
    assert (likes, dislikes) == (1, 0)
    likes, dislikes = cache.increment_reaction(1, 42, 'dislike', ttl_seconds=1)
    assert (likes, dislikes) == (1, 1)
    assert cache.get_reaction(1, 42) == {'likes': 1, 'dislikes': 1}

    cache.remove_reaction(1, 42)
    assert cache.get_reaction(1, 42) is None

    cache.init_reaction(1, 43, ttl_seconds=1)
    time.sleep(1.1)
    assert cache.get_reaction(1, 43) is None
    cache.conn.close()
