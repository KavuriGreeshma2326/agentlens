"""Health check router."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Health check")
def health_check() -> dict:
    """Return a simple liveness signal.

    Used by Docker Compose healthchecks, load balancers, and the
    frontend to verify the backend is reachable.
    """
    return {"status": "ok", "service": "agentlens"}
