"""Hello HTTP adapter."""

from fastapi import APIRouter, HTTPException

from jebaerme.models.hello import Hello
from jebaerme.services.hello import LlmAuthError, say_hello

router = APIRouter()


@router.get("/hello", response_model=Hello)
def hello() -> Hello:
    try:
        return say_hello()
    except LlmAuthError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
