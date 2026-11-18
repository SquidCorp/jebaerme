"""Qdrant client factory and connectivity checks."""

from typing import Protocol

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchAny,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)

from jebaerme.models.env import env

_QDRANT_TIMEOUT_SECONDS = 5
KNOWLEDGE_COLLECTION = "knowledge"
VECTOR_SIZE = 1536
PAYLOAD_INDEXES: tuple[tuple[str, PayloadSchemaType], ...] = (
    ("document_id", PayloadSchemaType.KEYWORD),
    ("source", PayloadSchemaType.KEYWORD),
    ("source_kind", PayloadSchemaType.KEYWORD),
    ("domain", PayloadSchemaType.KEYWORD),
    ("tags", PayloadSchemaType.KEYWORD),
    ("language", PayloadSchemaType.KEYWORD),
    ("content_hash", PayloadSchemaType.KEYWORD),
    ("source_ids", PayloadSchemaType.KEYWORD),
    ("chunk_index", PayloadSchemaType.INTEGER),
    ("source_priority", PayloadSchemaType.INTEGER),
    ("ingested_at", PayloadSchemaType.DATETIME),
)


class QdrantVectorSizeError(Exception):
    def __init__(self, actual: int) -> None:
        self.actual = actual
        super().__init__(
            f"Qdrant collection {KNOWLEDGE_COLLECTION} has vector size "
            f"{actual}, expected {VECTOR_SIZE}"
        )


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


def ensure_knowledge_collection(client: QdrantClient) -> None:
    if client.collection_exists(KNOWLEDGE_COLLECTION):
        vectors = client.get_collection(KNOWLEDGE_COLLECTION).config.params.vectors
        if not isinstance(vectors, VectorParams) or vectors.size != VECTOR_SIZE:
            actual = vectors.size if isinstance(vectors, VectorParams) else 0
            raise QdrantVectorSizeError(actual)
        return
    client.create_collection(
        collection_name=KNOWLEDGE_COLLECTION,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )
    for field_name, field_schema in PAYLOAD_INDEXES:
        try:
            client.create_payload_index(
                collection_name=KNOWLEDGE_COLLECTION,
                field_name=field_name,
                field_schema=field_schema,
            )
        except Exception:
            continue


def delete_points_by_document_id(client: QdrantClient, document_id: str) -> None:
    client.delete(
        collection_name=KNOWLEDGE_COLLECTION,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            )
        ),
    )


def existing_content_hashes(client: QdrantClient, hashes: list[str]) -> set[str]:
    if not hashes:
        return set()
    points, _offset = client.scroll(
        collection_name=KNOWLEDGE_COLLECTION,
        scroll_filter=Filter(
            must=[
                FieldCondition(
                    key="content_hash",
                    match=MatchAny(any=hashes),
                )
            ]
        ),
        limit=len(hashes),
        with_payload=["content_hash"],
        with_vectors=False,
    )
    found: set[str] = set()
    for point in points:
        payload = point.payload
        if payload is None:
            continue
        content_hash = payload.get("content_hash")
        if isinstance(content_hash, str):
            found.add(content_hash)
    return found


def upsert_points(client: QdrantClient, points: list[PointStruct]) -> None:
    if not points:
        return
    client.upsert(collection_name=KNOWLEDGE_COLLECTION, points=points)
