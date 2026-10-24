"""Decisions HTTP adapters."""

from fastapi import APIRouter, HTTPException

from jebaerme.models.intent import IntentRequest
from jebaerme.models.jev import BaseJevResponse
from jebaerme.services.intent import JevAuthError, classify_intent

router = APIRouter()


@router.post("/decisions/intent", response_model=BaseJevResponse)
def decisions_intent(body: IntentRequest) -> BaseJevResponse:
    try:
        return classify_intent(body.state)
    except JevAuthError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
