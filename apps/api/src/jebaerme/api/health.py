"""Health HTTP adapter."""

from fastapi import APIRouter

from jebaerme.models.health import Health
from jebaerme.services.health import get_health

router = APIRouter()


@router.get("/health", response_model=Health)
def health() -> Health:
    return get_health()
