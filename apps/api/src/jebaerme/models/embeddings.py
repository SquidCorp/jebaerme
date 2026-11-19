"""OpenRouter embedding response schemas. No I/O."""

from pydantic import BaseModel, ConfigDict


class OpenRouterEmbeddingItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    embedding: list[float]
    index: int = 0


class OpenRouterEmbeddingResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    data: list[OpenRouterEmbeddingItem]
