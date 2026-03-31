from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.transfer import Transfer, TransferStatus, TransferType
from app.repositories.account_repo import AccountRepository
from app.repositories.customer_repo import CustomerRepository
from app.repositories.transfer_repo import TransferRepository
from app.schemas.common import quantize_money

logger = logging.getLogger(__name__)

DEFAULT_CURRENCY = "EUR"


class BusinessRuleViolation(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=422, detail=detail)

class IntegrityError(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=409, detail=detail)


@dataclass(slots=True)
class BankingService:
    session: AsyncSession
    customers: CustomerRepository = field(init=False)
    accounts: AccountRepository = field(init=False)
    transfers: TransferRepository = field(init=False)

    def __post_init__(self) -> None:
        self.customers = CustomerRepository(self.session)
        self.accounts = AccountRepository(self.session)
        self.transfers = TransferRepository(self.session)

    async def list_customers(self, *, max_size: int, page: int):
        offset = (page - 1) * max_size
        return await self.customers.list_all(max_size=max_size, offset=offset)

    async def get_customer(self, customer_id: int):
        customer = await self.customers.get_with_accounts(customer_id)
        if customer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        return customer

    async def create_account(self, *, customer_id: int, initial_deposit: Decimal, requested_by: str) -> Account:
        customer = await self.customers.get(customer_id)
        if customer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

        amount = quantize_money(initial_deposit)
        account = await self.accounts.create(customer_id=customer_id, balance=amount, currency=DEFAULT_CURRENCY)

        self.session.add(Transfer(
            from_account_id=None,
            to_account_id=account.id,
            customer_id=customer_id,
            amount=amount,
            currency=DEFAULT_CURRENCY,
            type=TransferType.deposit,
            status=TransferStatus.completed,
            reference=f"initial_deposit:account:{account.id}",
            requested_by=requested_by,
            balance_after=amount,
            processed_at=datetime.now(UTC),
        ))
        await self.session.commit()
        logger.info("Account %s created for customer %s by %s (%.2f %s)", account.id, customer_id, requested_by, amount, DEFAULT_CURRENCY)
        return account

    async def get_balance(self, account_id: int) -> Account:
        account = await self.accounts.get(account_id)
        if account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        return account

    async def transfer(self, *, from_account_id: int, to_account_id: int, amount: Decimal, reference: str | None, requested_by: str) -> Transfer:
        if from_account_id == to_account_id:
            raise BusinessRuleViolation("from_account_id and to_account_id must be different")

        # Idempotency
        if reference is not None:
            existing = await self.transfers.get_existing_transfer_if_exists(
                from_account_id=from_account_id,
                to_account_id=to_account_id,
                reference=reference,
                amount=amount,)
            if existing is not None:
                raise IntegrityError('This transfer already exists')

        amount = quantize_money(amount)
        if amount <= 0:
            raise BusinessRuleViolation("Amount must be positive")
        
        

        # Lock accounts in deterministic order to prevent deadlocks
        first_id, second_id = sorted([from_account_id, to_account_id])
        first = await self.accounts.get_for_update(first_id)
        second = await self.accounts.get_for_update(second_id)
        lookup = {a.id: a for a in [first, second] if a is not None}
        source = lookup.get(from_account_id)
        destination = lookup.get(to_account_id)

        if source is None or destination is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        if source.balance < amount:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Insufficient funds: account {from_account_id} balance is {source.balance}, transfer requires {amount}",
            )

        source.balance = quantize_money(source.balance - amount)
        destination.balance = quantize_money(destination.balance + amount)

        transfer = Transfer(
            from_account_id=from_account_id,
            to_account_id=to_account_id,
            amount=amount,
            currency=DEFAULT_CURRENCY,
            type=TransferType.transfer,
            status=TransferStatus.completed,
            reference=reference,
            requested_by=requested_by,
            balance_after=source.balance,
            processed_at=datetime.now(UTC),
        )
        self.session.add(transfer)
        await self.session.commit()
        logger.info("Transfer %s: %s -> %s, %.2f %s by %s", transfer.id, from_account_id, to_account_id, amount, DEFAULT_CURRENCY, requested_by)
        return transfer

    async def transfer_history(self, account_id: int, *, max_size: int, page: int):
        account = await self.accounts.get(account_id)
        if account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        offset = (page - 1) * max_size
        return await self.transfers.list_for_account(account_id, max_size=max_size, offset=offset)
