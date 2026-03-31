from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_requested_by, require_api_key
from app.db.session import get_session
from app.schemas.transfer import TransferCreate, TransferRead
from app.services.banking import BankingService

router = APIRouter(prefix="", tags=["transfers"], dependencies=[Depends(require_api_key)])


@router.post(
    "/transfers",
    response_model=TransferRead,
    status_code=status.HTTP_201_CREATED,
    summary="Transfer money between accounts",
)
async def create_transfer(
    payload: TransferCreate,
    requested_by: str = Depends(get_requested_by),
    session: AsyncSession = Depends(get_session),
) -> TransferRead:
    service = BankingService(session)
    transfer = await service.transfer(
        from_account_id=payload.from_account_id,
        to_account_id=payload.to_account_id,
        amount=payload.amount,
        reference=payload.reference,
        requested_by=requested_by,
    )
    return TransferRead.model_validate(transfer)
