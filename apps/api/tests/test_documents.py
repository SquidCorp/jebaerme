from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from jebaerme.api.app import create_app
from jebaerme.db.qdrant import KNOWLEDGE_COLLECTION
from jebaerme.models.document import DocumentIngest
from jebaerme.services.documents import ingest_document
from jebaerme.services.embeddings import EmbeddingAuthError

_VECTOR_SIZE = 1536


def _fake_embed(texts: list[str]) -> list[list[float]]:
    return [[0.0] * _VECTOR_SIZE for _ in texts]


def _long_text() -> str:
    return "knowledge " * 150


def test_ingest_chunks_payload_dedup_and_replace() -> None:
    client = QdrantClient(":memory:")
    first = ingest_document(
        client,
        DocumentIngest(
            title="CV",
            text=_long_text(),
            source="cv",
            domain="technical",
            source_priority=80,
            source_ids=["cv/resume.md"],
        ),
        embed_texts=_fake_embed,
    )
    assert first.chunk_count >= 2
    assert first.skipped_chunks == 0

    points, _offset = client.scroll(
        collection_name=KNOWLEDGE_COLLECTION,
        scroll_filter=Filter(
            must=[FieldCondition(key="source", match=MatchValue(value="cv"))]
        ),
        limit=100,
        with_payload=True,
        with_vectors=False,
    )
    payloads = [point.payload or {} for point in points]
    payloads.sort(key=lambda payload: int(payload["chunk_index"]))
    assert [payload["chunk_index"] for payload in payloads][:2] == [0, 1]
    for payload in payloads:
        assert payload["domain"] == "technical"
        assert payload["source_priority"] == 80
        assert payload["source_ids"] == ["cv/resume.md"]
        assert payload["title"] == "CV"
        assert payload["text"]
        content_hash = payload["content_hash"]
        assert isinstance(content_hash, str)
        assert len(content_hash) == 64
        assert all(char in "0123456789abcdef" for char in content_hash)

    duplicate = ingest_document(
        client,
        DocumentIngest(
            title="Project notes",
            text=_long_text(),
            source="projects",
        ),
        embed_texts=_fake_embed,
    )
    assert duplicate.chunk_count == 0
    assert duplicate.skipped_chunks >= 1

    replacement_text = "replacement document body that is unique"
    replaced = ingest_document(
        client,
        DocumentIngest(
            title="CV",
            text=replacement_text,
            source="cv",
            document_id=first.document_id,
        ),
        embed_texts=_fake_embed,
    )
    assert replaced.document_id == first.document_id
    replaced_points, _offset = client.scroll(
        collection_name=KNOWLEDGE_COLLECTION,
        scroll_filter=Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=first.document_id),
                )
            ]
        ),
        limit=100,
        with_payload=True,
        with_vectors=False,
    )
    texts = [(point.payload or {}).get("text", "") for point in replaced_points]
    assert texts
    assert all(replacement_text in text for text in texts)
    assert all(_long_text() not in text for text in texts)


@pytest.fixture
def client(tmp_path: Path, monkeypatch: MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setattr("jebaerme.services.embeddings.embed_texts", _fake_embed)
    app = create_app(database_url=f"sqlite:///{tmp_path / 'test.db'}")
    with TestClient(app) as test_client:
        yield test_client


def test_create_document_endpoint(client: TestClient) -> None:
    response = client.post(
        "/documents",
        json={"title": "CV", "text": "hello knowledge", "source": "cv"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["document_id"]
    assert body["chunk_count"] == 1
    assert body["source"] == "cv"
    assert body["source_priority"] == 50


def test_create_document_rejects_unknown_source(client: TestClient) -> None:
    response = client.post(
        "/documents",
        json={"title": "x", "text": "hi", "source": "unknown"},
    )
    assert response.status_code == 422


def test_create_document_rejects_blank_text(client: TestClient) -> None:
    response = client.post(
        "/documents",
        json={"title": "x", "text": "   ", "source": "cv"},
    )
    assert response.status_code == 422


def test_create_document_requires_url_for_url_kind(client: TestClient) -> None:
    response = client.post(
        "/documents",
        json={
            "title": "x",
            "text": "hi",
            "source": "cv",
            "source_kind": "url",
        },
    )
    assert response.status_code == 422


def test_create_document_rejects_parent_source_ids(client: TestClient) -> None:
    response = client.post(
        "/documents",
        json={
            "title": "x",
            "text": "hi",
            "source": "cv",
            "source_ids": ["../secret"],
        },
    )
    assert response.status_code == 422


def test_create_document_maps_embedding_auth_error(
    client: TestClient, monkeypatch: MonkeyPatch
) -> None:
    def boom(_texts: list[str]) -> list[list[float]]:
        raise EmbeddingAuthError("OPENROUTER_API_KEY is not configured.")

    monkeypatch.setattr("jebaerme.services.embeddings.embed_texts", boom)
    response = client.post(
        "/documents",
        json={"title": "x", "text": "hi", "source": "cv"},
    )
    assert response.status_code == 502
    assert response.json() == {"detail": "OPENROUTER_API_KEY is not configured."}
