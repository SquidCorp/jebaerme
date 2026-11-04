"""Decisions HTTP adapters."""

from fastapi import APIRouter, HTTPException

from jebaerme.models.intent import IntentRequest
from jebaerme.models.jev import BaseJevResponse
from jebaerme.models.topic import TopicRequest
from jebaerme.services.intent import JevAuthError, classify_intent
from jebaerme.services.topic import filter_out_topic

router = APIRouter()


@router.post("/decisions/intent", response_model=BaseJevResponse)
def decisions_intent(body: IntentRequest) -> BaseJevResponse:
    try:
        return classify_intent(body.state)
    except JevAuthError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/decisions/topic", response_model=BaseJevResponse)
def decisions_topic(body: TopicRequest) -> BaseJevResponse:
    try:
        return filter_out_topic(body.state)
    except JevAuthError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
