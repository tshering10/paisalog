from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.dependencies import DbSession
from app.api.routers.endpoints import (
    analytics_router,
    auth_router,
    categories_router,
    transactions_router,
)
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Personal finance tracker backend.",
)

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


@app.get("/api/v1/health", tags=["health"])
def health_check(db: DbSession) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
