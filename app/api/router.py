from fastapi import APIRouter

from app.api.routes.accounts import router as accounts_router
from app.api.routes.customers import router as customers_router
from app.api.routes.health import router as health_router
from app.api.routes.transfers import router as transfers_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(customers_router)
api_router.include_router(accounts_router)
api_router.include_router(transfers_router)
