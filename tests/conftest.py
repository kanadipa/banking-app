from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_env_test = Path(__file__).resolve().parent.parent / ".env.test"
for line in _env_test.read_text().splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    key, _, value = line.partition("=")
    os.environ[key.strip()] = value.strip()

from app.core.config import settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_session  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Account, Customer, Transfer  # noqa: E402
from app.scripts.seed_customers import SEED_CUSTOMERS  # noqa: E402

engine = create_async_engine(settings.database_url, pool_pre_ping=True)
TestSession = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

HEADERS = {"X-API-Key": "test-key", "X-Requested-By": "test-runner"}

C1 = 1
C2 = 2
C3 = 3

def _run(coro):
    """Run a coroutine in a fresh event loop (for sync fixtures)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _make_engine():
    return create_async_engine(settings.database_url, pool_pre_ping=True)


@pytest.fixture(scope="session", autouse=True)
def _setup_db():
    """Create tables and seed customers once per test session (sync fixture)."""

    async def _up():
        engine = _make_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async with async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)() as session:
            async with session.begin():
                for row in SEED_CUSTOMERS:
                    session.add(Customer(id=row["id"], name=row["name"]))
        await engine.dispose()

    _run(_up())
    yield

    async def _down():
        engine = _make_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

    _run(_down())


@pytest_asyncio.fixture(autouse=True)
async def _clean_tables(_setup_db):
    """Clean up after each test."""
    yield
    engine = _make_engine()
    async with async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)() as session:
        async with session.begin():
            await session.execute(delete(Transfer))
            await session.execute(delete(Account))
            await session.execute(delete(Customer).where(Customer.id > 4))
            for row in SEED_CUSTOMERS:
                if await session.get(Customer, row["id"]) is None:
                    session.add(Customer(id=row["id"], name=row["name"]))
    await engine.dispose()


@pytest_asyncio.fixture()
async def client():
    """HTTPX test client with session override."""
    engine = _make_engine()
    test_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def override() -> AsyncIterator[AsyncSession]:
        async with test_session() as session:
            yield session

    app.dependency_overrides[get_session] = override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
    await engine.dispose()
