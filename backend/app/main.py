from fastapi import FastAPI
from app.api.dependencies import DbSession
from sqlalchemy import text
from app.api.routers.endpoints import (
    auth_router,
    categories_router,
    transactions_router,
)

app = FastAPI(
    title="PaisaLog API",
    version="0.1.0",
    description="Personal finance tracker backend.",
)

app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(transactions_router)

@app.get("/api/v1/health", tags=["health"])
def health_check(db: DbSession ) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
