"""FastAPI application entry point for OpenCitizen AI."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.api.routes.health import router as health_router
from app.core.config import settings
from app.core.errors import setup_exception_handlers
from app.db.session import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context for startup and shutdown events."""
    # Ensure database schema tables exist
    create_tables()
    yield
    # Teardown logic


def create_application() -> FastAPI:
    """Application factory for FastAPI instance."""
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Evidence-grounded civic intelligence platform backend API.",
        lifespan=lifespan,
    )

    # Register centralized exception handlers
    setup_exception_handlers(application)

    # CORS configuration
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check exposed at root level (/health)
    application.include_router(health_router)

    # API v1 routes (/api/v1/...)
    application.include_router(api_router, prefix=settings.API_V1_STR)

    @application.get("/", tags=["Root"])
    async def root() -> dict[str, str]:
        """Root status and documentation discovery endpoint."""
        return {
            "message": "Welcome to OpenCitizen AI API",
            "version": settings.VERSION,
            "docs_url": "/docs",
            "health_url": "/health",
        }

    return application


app = create_application()
