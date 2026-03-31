from __future__ import annotations

import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_api_key
from app.db.session import get_session
from app.schemas.customer import CustomerDetailRead, CustomerRead
from app.services.banking import BankingService

router = APIRouter(prefix="", tags=["customers"], dependencies=[Depends(require_api_key)])


@router.get("/customers", summary="List customers (paginated)")
async def list_customers(
    page: int = Query(default=1, ge=1),
    max_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    service = BankingService(session)
    customers, total = await service.list_customers(max_size=max_size, page=page)
    return {
        "items": [CustomerRead.model_validate(c) for c in customers],
        "total": total,
        "page": page,
        "max_size": max_size,
        "total_pages": math.ceil(total / max_size) if total > 0 else 1,
    }


@router.get(
    "/customers/{customer_id}",
    response_model=CustomerDetailRead,
    summary="Get customer with accounts",
)
async def get_customer(customer_id: int, session: AsyncSession = Depends(get_session)) -> CustomerDetailRead:
    service = BankingService(session)
    customer = await service.get_customer(customer_id)
    return CustomerDetailRead.model_validate(customer)
