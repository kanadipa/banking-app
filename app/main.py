from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.services.banking import BusinessRuleViolation, IntegrityError

logger = logging.getLogger(__name__)
configure_logging(settings.log_level)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Internal banking API for employee-facing customer account and transfer operations.",
)
app.include_router(api_router)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    errors = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err["loc"] if loc != "body")
        errors.append({"field": field or None, "message": err["msg"]})
    return JSONResponse(
        status_code=422,
        content={"error": "validation_error", "detail": "One or more fields failed validation.", "errors": errors},
    )


@app.exception_handler(BusinessRuleViolation)
async def business_rule_handler(_: Request, exc: BusinessRuleViolation) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "business_rule_violation", "detail": exc.detail},
    )


_ERROR_NAMES = {400: "bad_request", 401: "unauthorized", 403: "forbidden", 404: "not_found", 409: "insufficient_funds"}


@app.exception_handler(HTTPException)
async def http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": _ERROR_NAMES.get(exc.status_code, "http_error"), "detail": exc.detail},
    )


@app.exception_handler(SQLAlchemyError)
async def db_error_handler(_: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.exception("Database error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"error": "server_error", "detail": "An unexpected error occurred."},
    )

@app.exception_handler(IntegrityError)
async def integrity_error_handler(_: Request, exc: IntegrityError) -> JSONResponse:
    logger.warning("Integrity error (duplicate request): %s", exc)
    return JSONResponse(
        status_code=409,
        content={
            "error": "conflict",
            "detail": "Duplicate or conflicting request.",
        },
    )