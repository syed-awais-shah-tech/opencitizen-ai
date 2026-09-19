"""Health check endpoint routes."""

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.core.config import settings

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Health status response model."""

    status: str = Field(default="healthy", description="Service health state")
    service: str = Field(default="opencitizen-backend", description="Service identifier")
    version: str = Field(default="0.1.0", description="API version")
    environment: str = Field(default="development", description="Runtime environment")


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Returns the health status and metadata of the OpenCitizen backend service.",
)
async def get_health() -> HealthResponse:
    """Return service health status."""
    return HealthResponse(
        status="healthy",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
    )
