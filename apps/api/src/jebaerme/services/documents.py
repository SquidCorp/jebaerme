"""Document ingest: chunk, embed, and upsert into Qdrant."""

from collections.abc import Callable
from datetime import UTC, datetime
from hashlib import sha256
from typing import cast, get_args
from uuid import uuid4

from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import (
    FieldCondition,
    Filter,
    MatchAny,
    MatchValue,
    PointStruct,
    ScoredPoint,
)

from jebaerme.db.qdrant import (
    QdrantVectorSizeError,
    delete_points_by_document_id,
    ensure_knowledge_collection,
    existing_content_hashes,
    query_knowledge_points,
    upsert_points,
)
from jebaerme.models.document import (
    DocumentDomain,
    DocumentIngest,
    DocumentIngestPublic,
    DocumentSearch,
    DocumentSearchHit,
    DocumentSearchPublic,
    DocumentSource,
)
from jebaerme.services import embeddings as embeddings_service

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
CHUNK_LIMIT = 256


class CollectionConfigError(Exception):
    """Raised when the knowledge collection cannot be used."""


class DocumentIngestError(Exception):
    """Raised when a document cannot be chunked or ingested."""


def ingest_document(
    client: QdrantClient,
    payload: DocumentIngest,
    *,
    embed_texts: Callable[[list[str]], list[list[float]]] | None = None,
) -> DocumentIngestPublic:
    try:
        ensure_knowledge_collection(client)
    except QdrantVectorSizeError as exc:
        raise CollectionConfigError(
            f"Qdrant collection knowledge has vector size {exc.actual}, expected 1536"
        ) from exc

    chunks = [
        chunk
        for chunk in RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        ).split_text(payload.text)
        if chunk.strip()
    ]
    if not chunks:
        raise DocumentIngestError("document produced no chunks")
    if len(chunks) > CHUNK_LIMIT:
        raise DocumentIngestError("document produced too many chunks")

    document_id = payload.document_id or str(uuid4())
    if payload.document_id is not None:
        delete_points_by_document_id(client, document_id)

    hashes = [sha256(chunk.encode("utf-8")).hexdigest() for chunk in chunks]
    skipped = existing_content_hashes(client, hashes)
    remaining = [
        (index, chunk, content_hash)
        for index, (chunk, content_hash) in enumerate(zip(chunks, hashes, strict=True))
        if content_hash not in skipped
    ]
    embed = embed_texts if embed_texts is not None else embeddings_service.embed_texts
    vectors = embed([chunk for _, chunk, _ in remaining]) if remaining else []
    ingested_at = datetime.now(UTC).isoformat()
    points: list[PointStruct] = []
    point_ids: list[str] = []
    for (chunk_index, chunk, content_hash), vector in zip(
        remaining, vectors, strict=True
    ):
        point_id = str(uuid4())
        point_ids.append(point_id)
        points.append(
            PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "text": chunk,
                    "document_id": document_id,
                    "chunk_index": chunk_index,
                    "title": payload.title,
                    "source": payload.source,
                    "source_kind": payload.source_kind,
                    "url": payload.url,
                    "domain": payload.domain,
                    "tags": payload.tags,
                    "roles": payload.roles,
                    "language": payload.language,
                    "ingested_at": ingested_at,
                    "content_hash": content_hash,
                    "source_priority": payload.source_priority,
                    "source_ids": payload.source_ids,
                },
            )
        )
    upsert_points(client, points)
    return DocumentIngestPublic(
        document_id=document_id,
        title=payload.title,
        source=payload.source,
        domain=payload.domain,
        source_priority=payload.source_priority,
        chunk_count=len(points),
        skipped_chunks=len(chunks) - len(points),
        point_ids=point_ids,
    )


def _search_filter(payload: DocumentSearch) -> Filter | None:
    must: list[FieldCondition] = []
    if payload.sources:
        must.append(
            FieldCondition(key="source", match=MatchAny(any=list(payload.sources)))
        )
    if payload.domains:
        must.append(
            FieldCondition(key="domain", match=MatchAny(any=list(payload.domains)))
        )
    if payload.roles:
        must.append(FieldCondition(key="roles", match=MatchAny(any=payload.roles)))
    if payload.language is not None:
        must.append(
            FieldCondition(key="language", match=MatchValue(value=payload.language))
        )
    if not must:
        return None
    return Filter(must=must)


def _hit_from_point(point: ScoredPoint) -> DocumentSearchHit | None:
    payload = point.payload
    if not isinstance(payload, dict):
        return None
    text = payload.get("text")
    document_id = payload.get("document_id")
    title = payload.get("title")
    chunk_index = payload.get("chunk_index")
    source = payload.get("source")
    domain = payload.get("domain")
    if not isinstance(text, str):
        return None
    if not isinstance(document_id, str):
        return None
    if not isinstance(title, str):
        return None
    if not isinstance(chunk_index, int) or isinstance(chunk_index, bool):
        return None
    if source not in get_args(DocumentSource):
        return None
    if domain not in get_args(DocumentDomain):
        return None
    raw_roles = payload.get("roles", [])
    if not isinstance(raw_roles, list):
        return None
    roles = [item for item in raw_roles if isinstance(item, str)]
    return DocumentSearchHit(
        score=point.score,
        text=text,
        document_id=document_id,
        title=title,
        source=cast(DocumentSource, source),
        domain=cast(DocumentDomain, domain),
        roles=roles,
        chunk_index=chunk_index,
    )


def search_documents(
    client: QdrantClient,
    payload: DocumentSearch,
    *,
    embed_texts: Callable[[list[str]], list[list[float]]] | None = None,
) -> DocumentSearchPublic:
    try:
        ensure_knowledge_collection(client)
    except QdrantVectorSizeError as exc:
        raise CollectionConfigError(
            f"Qdrant collection knowledge has vector size {exc.actual}, expected 1536"
        ) from exc

    embed = embed_texts if embed_texts is not None else embeddings_service.embed_texts
    vector = embed([payload.question])[0]
    points = query_knowledge_points(
        client,
        vector,
        limit=payload.limit,
        score_threshold=payload.score_threshold,
        query_filter=_search_filter(payload),
    )
    hits = [
        hit for hit in (_hit_from_point(point) for point in points) if hit is not None
    ]
    return DocumentSearchPublic(hits=hits)
