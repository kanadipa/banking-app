from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.health import HealthRead

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthRead, summary="Health check")
async def health(session: AsyncSession = Depends(get_session)) -> HealthRead:
    await session.execute(text("SELECT 1"))
    return HealthRead(status="ok", database="up")
