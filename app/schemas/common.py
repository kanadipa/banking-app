from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from pydantic import Field
from pydantic.fields import FieldInfo

MONEY_QUANTIZER = Decimal("0.01")


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANTIZER, rounding=ROUND_HALF_UP)


def money_field(*, description: str = "Monetary amount") -> FieldInfo:
    return Field(..., gt=0, max_digits=12, decimal_places=2, description=description)


def money_read_field() -> FieldInfo:
    return Field(max_digits=12, decimal_places=2)
