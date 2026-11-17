"""Qdrant client factory and connectivity checks."""

from typing import Protocol

from qdrant_client import QdrantClient

from jebaerme.models.env import env

_QDRANT_TIMEOUT_SECONDS = 5


class QdrantClientLike(Protocol):
    def get_collections(self) -> object: ...

    def close(self) -> None: ...


def create_qdrant_client(url: str | None = None) -> QdrantClient:
    return QdrantClient(url=url or env.QDRANT_URL, timeout=_QDRANT_TIMEOUT_SECONDS)


def ensure_qdrant_ready(client: QdrantClientLike, *, url: str | None = None) -> None:
    try:
        client.get_collections()
    except Exception as exc:
        target = url or env.QDRANT_URL
        raise RuntimeError(f"Qdrant is unreachable at {target}") from exc


def qdrant_is_ready(client: QdrantClientLike) -> bool:
    try:
        client.get_collections()
    except Exception:
        return False
    return True


def close_qdrant_client(client: QdrantClientLike) -> None:
    client.close()
