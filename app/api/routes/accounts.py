from __future__ import annotations

import math

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_requested_by, require_api_key
from app.db.session import get_session
from app.schemas.account import AccountCreate, AccountRead, BalanceRead
from app.schemas.transfer import TransferHistoryItem, TransferPage
from app.services.banking import BankingService

router = APIRouter(prefix="", tags=["accounts"], dependencies=[Depends(require_api_key)])


@router.post(
    "/customers/{customer_id}/accounts",
    response_model=AccountRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a customer account with initial deposit",
)
async def create_account(
    customer_id: int,
    payload: AccountCreate,
    requested_by: str = Depends(get_requested_by),
    session: AsyncSession = Depends(get_session),
) -> AccountRead:
    service = BankingService(session)
    account = await service.create_account(
        customer_id=customer_id,
        initial_deposit=payload.initial_deposit,
        requested_by=requested_by,
    )
    return AccountRead.model_validate(account)


@router.get("/accounts/{account_id}/balance", response_model=BalanceRead, summary="Get account balance")
async def get_balance(account_id: int, session: AsyncSession = Depends(get_session)) -> BalanceRead:
    service = BankingService(session)
    account = await service.get_balance(account_id)
    return BalanceRead(account_id=account.id, customer_id=account.customer_id, balance=account.balance, currency=account.currency)


@router.get("/accounts/{account_id}/transfers", response_model=TransferPage, summary="Transfer history")
async def get_transfer_history(
    account_id: int,
    page: int = Query(default=1, ge=1),
    max_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> TransferPage:
    service = BankingService(session)
    items, total = await service.transfer_history(account_id, max_size=max_size, page=page)

    history = []
    for t in items:
        is_outgoing = t.from_account_id == account_id
        counterparty_id = t.to_account_id if is_outgoing else t.from_account_id
        counterparty_customer_id = None
        if counterparty_id is not None:
            cp = await service.accounts.get(counterparty_id)
            if cp is not None:
                counterparty_customer_id = cp.customer_id

        history.append(TransferHistoryItem(
            id=t.id,
            direction="outgoing" if is_outgoing else "incoming",
            account_id=account_id,
            customer_id=t.from_account_id if is_outgoing else t.to_account_id,
            counterparty_account_id=counterparty_id,
            counterparty_customer_id=counterparty_customer_id,
            amount=t.amount,
            balance_after=t.balance_after,
            currency=t.currency,
            type=t.type,
            reference=t.reference,
            requested_by=t.requested_by,
            created_at=t.created_at,
        ))

    return TransferPage(
        items=history,
        total=total,
        page=page,
        max_size=max_size,
        total_pages=math.ceil(total / max_size) if total > 0 else 1,
    )
