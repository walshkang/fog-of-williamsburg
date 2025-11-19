from fastapi import APIRouter

from ..config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health", summary="Health check")
async def health_check() -> dict:
    """Simple health-check endpoint for uptime and environment verification."""
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }


