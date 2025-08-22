import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from bot.database import Base
from bot.models import AdminUser
from bot.utils import admins


@pytest_asyncio.fixture
async def admin_session(monkeypatch):
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    monkeypatch.setattr(admins, "SessionLocal", TestingSessionLocal)
    yield TestingSessionLocal
    await engine.dispose()


@pytest.mark.asyncio
async def test_is_user_admin_db(admin_session):
    async with admin_session() as session:
        session.add(
            AdminUser(user_id="1", full_name="Admin", username="admin", is_active=True)
        )
        session.add(
            AdminUser(user_id="3", full_name="Inactive", username="inactive", is_active=False)
        )
        await session.commit()

    assert await admins.is_user_admin_db(1) is True
    assert await admins.is_user_admin_db(2) is False
    assert await admins.is_user_admin_db(3) is False
