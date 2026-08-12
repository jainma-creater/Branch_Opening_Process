from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import (
    accounts,
    agreements,
    approvals,
    auth,
    cc,
    completion,
    deposits,
    loa,
    openings,
    organization,
    payment,
    procurement,
    properties,
    reports,
    workflow,
)
from app.api.health import router as health_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import RequestContextMiddleware


def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
    )
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(Exception, generic_exception_handler)
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(organization.router, prefix="/api/v1")
    app.include_router(openings.router, prefix="/api/v1")
    app.include_router(workflow.router, prefix="/api/v1")
    app.include_router(approvals.router, prefix="/api/v1")
    app.include_router(properties.router, prefix="/api/v1")
    app.include_router(deposits.router, prefix="/api/v1")
    app.include_router(loa.router, prefix="/api/v1")
    app.include_router(agreements.router, prefix="/api/v1")
    app.include_router(procurement.router, prefix="/api/v1")
    app.include_router(accounts.router, prefix="/api/v1")
    app.include_router(cc.router, prefix="/api/v1")
    app.include_router(payment.router, prefix="/api/v1")
    app.include_router(completion.router, prefix="/api/v1")
    app.include_router(reports.router, prefix="/api/v1")
    return app


app = create_app()