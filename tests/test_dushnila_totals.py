"""Unit tests for score aggregation floor (score can't go below 0)."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bot.database import Base
from bot.utils import dushnila_engine


@pytest_asyncio.fixture
async def dushnila_db(monkeypatch):
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    from bot import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    monkeypatch.setattr(dushnila_engine, "SessionLocal", TestingSessionLocal)
    yield TestingSessionLocal
    await engine.dispose()


async def _add_event(session_local, **overrides):
    from bot.models import DushnilaEvent

    defaults = dict(
        chat_id=123,
        user_id=7,
        full_name="Masha",
        username="masha",
        category="anti",
        reason="фраза «спасибо»",
        points=-2,
    )
    defaults.update(overrides)
    async with session_local() as session:
        session.add(DushnilaEvent(**defaults))
        await session.commit()


@pytest.mark.asyncio
async def test_weekly_totals_floor_at_zero(dushnila_db):
    await _add_event(dushnila_db, points=-15, reason="фраза «релизим»")

    totals = await dushnila_engine.get_weekly_totals(123)

    assert len(totals) == 1
    assert totals[0][3] == 0


@pytest.mark.asyncio
async def test_weekly_totals_positive_sum_unaffected(dushnila_db):
    await _add_event(
        dushnila_db, points=10, category="phrase", reason="фраза «это баг»"
    )
    await _add_event(dushnila_db, points=-3, category="anti", reason="фраза «согласен»")

    totals = await dushnila_engine.get_weekly_totals(123)

    assert totals[0][3] == 7


@pytest.mark.asyncio
async def test_today_totals_floor_at_zero(dushnila_db):
    await _add_event(dushnila_db, points=-10, reason="фраза «можно закрывать»")

    totals = await dushnila_engine.get_today_totals(123)

    assert len(totals) == 1
    assert totals[0][3] == 0


@pytest.mark.asyncio
async def test_personal_weekly_total_floor_at_zero(dushnila_db):
    await _add_event(dushnila_db, points=-5, reason="фраза «всё ок»")
    await _add_event(dushnila_db, points=-2, reason="фраза «спасибо»")

    total = await dushnila_engine.get_personal_weekly_total(123, 7)

    assert total == 0


@pytest.mark.asyncio
async def test_personal_weekly_total_positive_sum_unaffected(dushnila_db):
    await _add_event(
        dushnila_db, points=20, category="phrase", reason="фраза «это баг»"
    )
    await _add_event(dushnila_db, points=-2, reason="фраза «спасибо»")

    total = await dushnila_engine.get_personal_weekly_total(123, 7)

    assert total == 18
