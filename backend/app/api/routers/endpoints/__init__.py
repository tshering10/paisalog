from app.api.routers.endpoints.auth import router as auth_router
from app.api.routers.endpoints.categories import router as categories_router

__all__ = ["auth_router", "categories_router"]