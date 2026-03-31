from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.schemas.common import money_read_field


class CustomerAccountSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    balance: Decimal = money_read_field()
    currency: str


class CustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class CustomerDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    accounts: list[CustomerAccountSummary] = []
