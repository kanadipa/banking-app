from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account


class AccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get(self, account_id: int) -> Account | None:
        result = await self._s.execute(select(Account).where(Account.id == account_id))
        return result.scalar_one_or_none()

    async def get_for_update(self, account_id: int) -> Account | None:
        result = await self._s.execute(
            select(Account).where(Account.id == account_id).with_for_update()
        )
        return result.scalar_one_or_none()

    async def create(self, *, customer_id: int, balance, currency: str) -> Account:
        account = Account(customer_id=customer_id, balance=balance, currency=currency)
        self._s.add(account)
        await self._s.flush()
        return account
