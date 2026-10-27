"""Chat request schema."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, description="User message to send to the agent.")


class ChatState(BaseModel):
    message: str = Field(min_length=1, description="User message to send to the agent.")
    intent: str | None = None
    intent_instruction: str | None = None
    response: str | None = None
