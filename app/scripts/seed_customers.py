from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.db.session import async_session_factory
from app.models.customer import Customer

SEED_CUSTOMERS = [
    {"id": 1, "name": "Arisha Barron"},
    {"id": 2, "name": "Branden Gibson"},
    {"id": 3, "name": "Rhonda Church"},
    {"id": 4, "name": "Georgina Hazel"},
]


async def seed() -> None:
    async with async_session_factory() as session:
        async with session.begin():
            existing = set((await session.execute(select(Customer.id))).scalars().all())
            for row in SEED_CUSTOMERS:
                if row["id"] not in existing:
                    session.add(Customer(id=row["id"], name=row["name"]))


if __name__ == "__main__":
    asyncio.run(seed())
