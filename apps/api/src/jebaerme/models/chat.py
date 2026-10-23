"""Chat request schema."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, description="User message to send to the agent.")
