from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transfer import Transfer

from decimal import Decimal


class TransferRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_by_reference(self, reference: str) -> Transfer | None:
        result = await self._s.execute(select(Transfer).where(Transfer.reference == reference))
        return result.scalar_one_or_none()

    async def list_for_account(self, account_id: int, *, max_size: int, offset: int) -> tuple[list[Transfer], int]:
        where = (Transfer.from_account_id == account_id) | (Transfer.to_account_id == account_id)
        rows = await self._s.execute(
            select(Transfer).where(where).order_by(Transfer.created_at.desc(), Transfer.id.desc()).limit(max_size).offset(offset)
        )
        total = await self._s.scalar(
            select(func.count()).select_from(select(Transfer.id).where(where).subquery())
        )
        return list(rows.scalars().all()), int(total or 0)

    async def get_existing_transfer_if_exists(
        self,
        *,
        from_account_id: int,
        to_account_id: int,
        reference: str | None,
        amount: Decimal,
    ) -> Transfer | None:
        return await self._s.scalar(
            select(Transfer).where(
                Transfer.from_account_id == from_account_id,
                Transfer.to_account_id == to_account_id,
                Transfer.amount == amount,
                Transfer.reference == reference,
        )
    )