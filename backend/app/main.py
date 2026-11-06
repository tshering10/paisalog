import logging
import secrets

from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.dependencies import DbSession
from app.api.routers.endpoints import (
    analytics_router,
    auth_router,
    budgets_router,
    categories_router,
    transactions_router,
)
from app.core.config import get_settings
from app.core.observability import (
    configure_logging,
    get_pool_metrics,
    get_request_metrics,
    handle_unexpected_error,
    log_request,
)
from app.db.session import engine

settings = get_settings()
configure_logging()
logger = logging.getLogger("app.health")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Personal finance tracker backend.",
)
app.add_exception_handler(Exception, handle_unexpected_error)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(transactions_router)
app.include_router(analytics_router)
app.include_router(budgets_router)
app.middleware("http")(log_request)


@app.get("/api/v1/health/live", tags=["health"])
def liveness_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/health/ready", tags=["health"], response_model=None)
def readiness_check(db: DbSession) -> dict[str, str] | JSONResponse:
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        logger.exception("readiness_check_failed")
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready"},
        )
    return {"status": "ready"}


@app.get("/api/v1/health", tags=["health"], include_in_schema=False)
def health_check(db: DbSession) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.get("/api/v1/metrics", tags=["observability"], response_model=None)
def metrics_check(
    metrics_key: str | None = Header(default=None, alias="X-Metrics-Key"),
) -> dict[str, object]:
    configured_key = settings.metrics_api_key
    if (
        configured_key is None
        or metrics_key is None
        or not secrets.compare_digest(metrics_key, configured_key)
    ):
        return JSONResponse(status_code=404, content={"detail": "Not found"})
    return {
        "routes": get_request_metrics()["routes"],
        "database_pool": get_pool_metrics(engine.pool, settings.db_max_overflow),
    }
