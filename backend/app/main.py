from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.limits import limiter
from app.middleware import RequestIdMiddleware
from app.routers import (
    admin,
    agribusiness,
    analytics,
    auth,
    channels,
    copilot,
    farms,
    lender,
    notifications,
    risk_products,
    sensors,
    vision,
)
from app.utils.logging import configure_logging

logger = logging.getLogger("agribud")

configure_logging("INFO" if settings.environment != "development" else "DEBUG")
app = FastAPI(title=settings.app_name)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RequestIdMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(farms.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(copilot.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(agribusiness.router, prefix="/api/v1")
app.include_router(lender.router, prefix="/api/v1")
app.include_router(sensors.router, prefix="/api/v1")
app.include_router(vision.router, prefix="/api/v1")
app.include_router(channels.router, prefix="/api/v1")
app.include_router(risk_products.router, prefix="/api/v1")


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc.detail), "code": "HTTP_ERROR"},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "code": "VALIDATION_ERROR",
            "errors": jsonable_encoder(exc.errors()),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled server error", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "code": "INTERNAL_SERVER_ERROR"},
    )


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}


@app.get("/healthz")
async def liveness() -> dict:
    return {"status": "ok"}


@app.get("/readyz")
async def readiness() -> dict:
    checks: dict[str, str] = {}
    overall = "ok"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc.__class__.__name__}"
        overall = "degraded"
    return {"status": overall, "checks": checks}


@app.get("/metrics")
async def metrics() -> JSONResponse:
    """Lightweight JSON metrics. Swap for prometheus_client in production."""
    import os

    rss_bytes = 0
    try:
        import resource  # type: ignore[import-not-found]

        rss_bytes = int(
            getattr(resource.getrusage(resource.RUSAGE_SELF), "ru_maxrss", 0)
        )
    except ImportError:
        # Windows: fall back to ctypes GetProcessMemoryInfo.
        try:
            import ctypes
            from ctypes import wintypes

            class _PMC(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            pmc = _PMC()
            pmc.cb = ctypes.sizeof(_PMC)
            if ctypes.windll.psapi.GetProcessMemoryInfo(
                ctypes.windll.kernel32.GetCurrentProcess(),
                ctypes.byref(pmc),
                pmc.cb,
            ):
                rss_bytes = int(pmc.WorkingSetSize)
        except Exception:
            rss_bytes = 0

    return JSONResponse(
        {
            "process": {
                "pid": os.getpid(),
                "memory_rss_bytes": rss_bytes,
                "num_threads": 1,
            },
            "app": {
                "name": settings.app_name,
                "environment": settings.environment,
            },
        }
    )
