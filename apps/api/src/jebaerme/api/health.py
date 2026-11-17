"""Health HTTP adapter."""

from fastapi import APIRouter, Request

from jebaerme.models.health import Health
from jebaerme.services.health import get_health

router = APIRouter()


@router.get("/health", response_model=Health)
def health(request: Request) -> Health:
    return get_health(qdrant_client=getattr(request.app.state, "qdrant", None))
