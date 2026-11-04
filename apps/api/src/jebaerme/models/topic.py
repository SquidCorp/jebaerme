"""Topic classification request schema."""

from pydantic import BaseModel, Field


class TopicRequest(BaseModel):
    state: str = Field(min_length=1, description="The input to evaluate")
