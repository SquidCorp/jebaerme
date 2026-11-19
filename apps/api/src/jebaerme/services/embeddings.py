"""OpenRouter embedding client."""

import requests

from jebaerme.models.embeddings import OpenRouterEmbeddingResponse
from jebaerme.models.env import env

EMBEDDINGS_URL = "https://openrouter.ai/api/v1/embeddings"
_VECTOR_SIZE = 1536


class EmbeddingAuthError(RuntimeError):
    """The embeddings API rejected or is missing the configured API key."""


class EmbeddingError(RuntimeError):
    """The embeddings API returned an unusable response."""


def embed_texts(texts: list[str]) -> list[list[float]]:
    api_key = env.openrouter_api_key()
    if api_key is None:
        raise EmbeddingAuthError("OPENROUTER_API_KEY is not configured.")
    response = requests.post(
        EMBEDDINGS_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": env.EMBEDDING_MODEL,
            "input": texts,
            "dimensions": _VECTOR_SIZE,
            "encoding_format": "float",
            "input_type": "search_document",
        },
        timeout=30,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        if response.status_code == 401:
            raise EmbeddingAuthError(
                "OpenRouter rejected OPENROUTER_API_KEY (401)."
            ) from exc
        reason = response.reason or str(exc)
        raise EmbeddingError(f"{response.status_code} {reason}") from exc
    try:
        parsed = OpenRouterEmbeddingResponse.model_validate(response.json())
    except (ValueError, requests.JSONDecodeError) as exc:
        reason = response.reason or "invalid JSON"
        raise EmbeddingError(f"{response.status_code} {reason}") from exc
    data = sorted(parsed.data, key=lambda item: item.index)
    if len(data) != len(texts):
        raise EmbeddingError(f"{response.status_code} unexpected embedding count")
    embeddings: list[list[float]] = []
    for item in data:
        if len(item.embedding) != _VECTOR_SIZE:
            raise EmbeddingError(
                f"{response.status_code} unexpected embedding dimensions"
            )
        embeddings.append(item.embedding)
    return embeddings
