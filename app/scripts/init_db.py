"""Create tables and seed customers. Safe to run repeatedly."""
from __future__ import annotations

import asyncio
from app.db.base import Base
from app.db.session import engine
from app.models import Account, Customer, Transfer  # noqa: F401 — register models
from app.scripts.seed_customers import seed


async def init() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed()


if __name__ == "__main__":
    asyncio.run(init())
