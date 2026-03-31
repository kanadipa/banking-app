from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.schemas.common import money_field, money_read_field


class AccountCreate(BaseModel):
    initial_deposit: Decimal = money_field(description="Initial deposit amount in EUR")


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_id: int
    balance: Decimal = money_read_field()
    currency: str
    created_at: datetime
    updated_at: datetime


class BalanceRead(BaseModel):
    account_id: int
    customer_id: int
    balance: Decimal = money_read_field()
    currency: str
