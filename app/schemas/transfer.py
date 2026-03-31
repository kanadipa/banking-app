from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.transfer import TransferStatus, TransferType
from app.schemas.common import money_field, money_read_field


class TransferCreate(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: Decimal = money_field(description="Transfer amount in EUR")
    reference: str | None = Field(default=None, max_length=255)


class TransferRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    from_account_id: int | None
    to_account_id: int | None
    customer_id: int | None
    amount: Decimal = money_read_field()
    balance_after: Decimal = money_read_field()
    currency: str
    type: TransferType
    status: TransferStatus
    reference: str | None
    requested_by: str
    created_at: datetime
    processed_at: datetime | None


class TransferHistoryItem(BaseModel):
    """Transfer as seen from a specific account's perspective."""
    id: int
    direction: str
    customer_id: int | None
    counterparty_account_id: int | None
    counterparty_customer_id: int | None
    amount: Decimal = money_read_field()
    balance_after: Decimal | None = money_read_field()
    currency: str
    type: TransferType
    reference: str | None
    requested_by: str
    created_at: datetime


class TransferPage(BaseModel):
    items: list[TransferHistoryItem]
    total: int
    page: int
    max_size: int
    total_pages: int
