from app.api.routers.endpoints.analytics import router as analytics_router
from app.api.routers.endpoints.auth import router as auth_router
from app.api.routers.endpoints.budgets import router as budgets_router
from app.api.routers.endpoints.categories import router as categories_router
from app.api.routers.endpoints.transactions import router as transactions_router

__all__ = [
    "analytics_router",
    "auth_router",
    "budgets_router",
    "categories_router",
    "transactions_router",
]
