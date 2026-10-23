"""Agent configuration schemas."""

from pydantic import BaseModel, ConfigDict, Field


class AgentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str = Field(description="OpenRouter model id.")
    temperature: float = Field(default=0.9, description="Sampling temperature.")
    max_retries: int | None = Field(default=None, description="Optional retry cap.")


class AgentPrompt(BaseModel):
    prompt: str = Field(description="Text sent to the model.")
