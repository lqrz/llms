"""Server routes."""

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health():
    """
    Basic health check endpoint.

    Returns:
        Simple status message indicating the service is running
    """
    return {"status": "healthy", "service": "finance-ai-backend"}
