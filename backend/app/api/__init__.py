"""Top-level API router configuration."""

from fastapi import APIRouter

from app.api.routes.analytics import router as analytics_router
from app.api.routes.datasets import router as datasets_router
from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.api.routes.orchestration import router as orchestration_router
from app.api.routes.query import router as query_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(datasets_router)
api_router.include_router(documents_router)
api_router.include_router(query_router)
api_router.include_router(analytics_router)
api_router.include_router(orchestration_router)

__all__ = ["api_router"]
