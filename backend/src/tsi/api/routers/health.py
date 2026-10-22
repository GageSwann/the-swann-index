from fastapi import APIRouter

router = APIRouter()


@router.get("/health", include_in_schema=False)
def get_health() -> dict[str, str]:
    """Liveness for the host's health check. No database call: Neon suspends idle
    compute, and a sleeping database shouldn't mark the API as down."""
    return {"status": "ok"}
