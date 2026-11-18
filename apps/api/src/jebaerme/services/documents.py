"""Document ingest: chunk, embed, and upsert into Qdrant."""

from collections.abc import Callable
from datetime import UTC, datetime
from hashlib import sha256
from uuid import uuid4

from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

from jebaerme.db.qdrant import (
    QdrantVectorSizeError,
    delete_points_by_document_id,
    ensure_knowledge_collection,
    existing_content_hashes,
    upsert_points,
)
from jebaerme.models.document import DocumentIngest, DocumentIngestPublic
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
