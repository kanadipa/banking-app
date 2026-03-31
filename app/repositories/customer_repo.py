from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import Customer


class CustomerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get(self, customer_id: int) -> Customer | None:
        result = await self._s.execute(select(Customer).where(Customer.id == customer_id))
        return result.scalar_one_or_none()

    async def get_with_accounts(self, customer_id: int) -> Customer | None:
        result = await self._s.execute(
            select(Customer).where(Customer.id == customer_id).options(selectinload(Customer.accounts))
        )
        return result.scalar_one_or_none()

    async def list_all(self, *, max_size: int, offset: int) -> tuple[list[Customer], int]:
        rows = await self._s.execute(select(Customer).order_by(Customer.name).limit(max_size).offset(offset))
        total = await self._s.scalar(select(func.count()).select_from(Customer))
        return list(rows.scalars().all()), int(total or 0)
