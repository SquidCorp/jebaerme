"""Chat and hello HTTP adapters."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from jebaerme.models.chat import ChatRequest
from jebaerme.models.hello import Hello
from jebaerme.services.chat import LlmAuthError, stream_chat
from jebaerme.services.hello import say_hello

router = APIRouter()


@router.get("/hello", response_model=Hello)
def hello() -> Hello:
    try:
        return say_hello()
    except LlmAuthError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/chat")
async def chat(body: ChatRequest) -> StreamingResponse:
    try:
        tokens = await stream_chat(body.message)
    except LlmAuthError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return StreamingResponse(tokens, media_type="text/plain; charset=utf-8")
