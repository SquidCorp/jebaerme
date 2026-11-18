from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from jebaerme.api.app import create_app
from jebaerme.db.qdrant import KNOWLEDGE_COLLECTION
from jebaerme.models.document import DocumentIngest, DocumentSearch
from jebaerme.services.documents import ingest_document, search_documents
from jebaerme.services.embeddings import EmbeddingAuthError

_VECTOR_SIZE = 1536


def _fake_embed(texts: list[str]) -> list[list[float]]:
    return [[0.0] * _VECTOR_SIZE for _ in texts]


def _unit(index: int) -> list[list[float]]:
    vector = [0.0] * _VECTOR_SIZE
    vector[index] = 1.0
    return [vector]


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
            roles=["Staff Engineer"],
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
        assert payload["roles"] == ["Staff Engineer"]
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


def test_create_document_defaults_roles(client: TestClient) -> None:
    response = client.post(
        "/documents",
        json={"title": "x", "text": "hi", "source": "cv"},
    )
    assert response.status_code == 201


def test_create_document_drops_empty_roles(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setattr("jebaerme.services.embeddings.embed_texts", _fake_embed)
    qdrant = QdrantClient(":memory:")
    app = create_app(
        database_url=f"sqlite:///{tmp_path / 'roles.db'}",
        qdrant_client=qdrant,
    )
    with TestClient(app) as test_client:
        response = test_client.post(
            "/documents",
            json={
                "title": "x",
                "text": "hi",
                "source": "cv",
                "roles": ["Staff Engineer", ""],
            },
        )
        assert response.status_code == 201
        points, _offset = qdrant.scroll(
            collection_name=KNOWLEDGE_COLLECTION,
            limit=100,
            with_payload=True,
            with_vectors=False,
        )
    assert points
    for point in points:
        assert (point.payload or {})["roles"] == ["Staff Engineer"]


def test_search_ranks_by_similarity() -> None:
    client = QdrantClient(":memory:")
    doc_a = ingest_document(
        client,
        DocumentIngest(title="Alpha CV", text="alpha knowledge", source="cv"),
        embed_texts=lambda texts: _unit(0),
    )
    ingest_document(
        client,
        DocumentIngest(
            title="Beta project",
            text="beta knowledge",
            source="projects",
        ),
        embed_texts=lambda texts: _unit(1),
    )
    result = search_documents(
        client,
        DocumentSearch(question="alpha"),
        embed_texts=lambda texts: _unit(0),
    )
    assert result.hits
    assert "alpha" in result.hits[0].text
    assert result.hits[0].source == "cv"
    assert result.hits[0].document_id == doc_a.document_id
    assert isinstance(result.hits[0].score, float)
    if len(result.hits) > 1:
        assert result.hits[0].score > result.hits[1].score
    for hit in result.hits:
        dumped = hit.model_dump()
        assert {"title", "domain", "roles", "chunk_index"} <= dumped.keys()
        assert isinstance(hit.roles, list)
        assert isinstance(hit.chunk_index, int)
    assert "point_ids" not in result.model_dump()


def test_search_filters() -> None:
    source_client = QdrantClient(":memory:")
    ingest_document(
        source_client,
        DocumentIngest(title="A", text="alpha knowledge", source="cv"),
        embed_texts=lambda texts: _unit(0),
    )
    ingest_document(
        source_client,
        DocumentIngest(title="B", text="beta knowledge", source="projects"),
        embed_texts=lambda texts: _unit(1),
    )
    by_source = search_documents(
        source_client,
        DocumentSearch(question="alpha", sources=["cv"]),
        embed_texts=lambda texts: _unit(0),
    )
    assert by_source.hits
    assert all(hit.source == "cv" for hit in by_source.hits)

    domain_client = QdrantClient(":memory:")
    ingest_document(
        domain_client,
        DocumentIngest(
            title="T",
            text="tech knowledge",
            source="cv",
            domain="technical",
        ),
        embed_texts=lambda texts: _unit(0),
    )
    ingest_document(
        domain_client,
        DocumentIngest(
            title="G",
            text="gen knowledge",
            source="cv",
            domain="general",
        ),
        embed_texts=lambda texts: _unit(0),
    )
    by_domain = search_documents(
        domain_client,
        DocumentSearch(question="q", domains=["technical"]),
        embed_texts=lambda texts: _unit(0),
    )
    assert by_domain.hits
    assert all(hit.domain == "technical" for hit in by_domain.hits)

    roles_client = QdrantClient(":memory:")
    ingest_document(
        roles_client,
        DocumentIngest(
            title="Staff",
            text="staff knowledge",
            source="cv",
            roles=["Staff Engineer"],
        ),
        embed_texts=lambda texts: _unit(0),
    )
    ingest_document(
        roles_client,
        DocumentIngest(
            title="Product",
            text="product knowledge",
            source="cv",
            roles=["Product"],
        ),
        embed_texts=lambda texts: _unit(0),
    )
    by_role = search_documents(
        roles_client,
        DocumentSearch(question="q", roles=["Staff Engineer"]),
        embed_texts=lambda texts: _unit(0),
    )
    assert len(by_role.hits) == 1
    assert by_role.hits[0].roles == ["Staff Engineer"]
    by_roles_any = search_documents(
        roles_client,
        DocumentSearch(question="q", roles=["Staff Engineer", "Tech Lead"]),
        embed_texts=lambda texts: _unit(0),
    )
    assert any(hit.roles == ["Staff Engineer"] for hit in by_roles_any.hits)

    lang_client = QdrantClient(":memory:")
    ingest_document(
        lang_client,
        DocumentIngest(
            title="EN",
            text="english knowledge",
            source="cv",
            language="en",
        ),
        embed_texts=lambda texts: _unit(0),
    )
    ingest_document(
        lang_client,
        DocumentIngest(
            title="FR",
            text="french knowledge",
            source="cv",
            language="fr",
        ),
        embed_texts=lambda texts: _unit(0),
    )
    by_lang = search_documents(
        lang_client,
        DocumentSearch(question="q", language="fr"),
        embed_texts=lambda texts: _unit(0),
    )
    assert by_lang.hits
    assert all("french" in hit.text for hit in by_lang.hits)

    and_client = QdrantClient(":memory:")
    ingest_document(
        and_client,
        DocumentIngest(
            title="CV EN",
            text="cv en knowledge",
            source="cv",
            language="en",
        ),
        embed_texts=lambda texts: _unit(0),
    )
    ingest_document(
        and_client,
        DocumentIngest(
            title="CV FR",
            text="cv fr knowledge",
            source="cv",
            language="fr",
        ),
        embed_texts=lambda texts: _unit(0),
    )
    ingest_document(
        and_client,
        DocumentIngest(
            title="Project EN",
            text="proj en knowledge",
            source="projects",
            language="en",
        ),
        embed_texts=lambda texts: _unit(0),
    )
    combined = search_documents(
        and_client,
        DocumentSearch(question="q", sources=["cv"], language="en"),
        embed_texts=lambda texts: _unit(0),
    )
    assert combined.hits
    assert all(hit.source == "cv" and "cv en" in hit.text for hit in combined.hits)


def test_search_limit_and_score_threshold() -> None:
    client = QdrantClient(":memory:")
    doc_a = ingest_document(
        client,
        DocumentIngest(title="A", text="alpha knowledge", source="cv"),
        embed_texts=lambda texts: _unit(0),
    )
    ingest_document(
        client,
        DocumentIngest(title="B", text="beta knowledge", source="projects"),
        embed_texts=lambda texts: _unit(1),
    )
    limited = search_documents(
        client,
        DocumentSearch(question="alpha", limit=1),
        embed_texts=lambda texts: _unit(0),
    )
    assert len(limited.hits) == 1
    assert limited.hits[0].document_id == doc_a.document_id

    thresholded = search_documents(
        client,
        DocumentSearch(question="alpha", score_threshold=0.5),
        embed_texts=lambda texts: _unit(0),
    )
    assert [hit.document_id for hit in thresholded.hits] == [doc_a.document_id]

    both = search_documents(
        client,
        DocumentSearch(question="alpha", score_threshold=None),
        embed_texts=lambda texts: _unit(0),
    )
    assert len(both.hits) == 2


def test_search_empty_corpus() -> None:
    client = QdrantClient(":memory:")
    result = search_documents(
        client,
        DocumentSearch(question="x"),
        embed_texts=lambda texts: _unit(0),
    )
    assert result.hits == []


def test_search_endpoint_returns_hits_list(client: TestClient) -> None:
    response = client.post("/documents/search", json={"question": "x"})
    assert response.status_code == 200
    assert isinstance(response.json()["hits"], list)


def test_search_endpoint_rejects_blank_question(client: TestClient) -> None:
    response = client.post("/documents/search", json={"question": "   "})
    assert response.status_code == 422


def test_search_endpoint_rejects_unknown_source(client: TestClient) -> None:
    response = client.post(
        "/documents/search",
        json={"question": "x", "sources": ["nope"]},
    )
    assert response.status_code == 422


def test_search_endpoint_returns_ingested_document(client: TestClient) -> None:
    created = client.post(
        "/documents",
        json={"title": "CV", "text": "hello knowledge", "source": "cv"},
    )
    assert created.status_code == 201
    response = client.post(
        "/documents/search",
        json={"question": "x", "limit": 8},
    )
    assert response.status_code == 200
    hits = response.json()["hits"]
    assert len(hits) >= 1
    assert hits[0]["text"]
    assert hits[0]["document_id"]
    assert "score" in hits[0]


def test_search_endpoint_maps_embedding_auth_error(
    client: TestClient, monkeypatch: MonkeyPatch
) -> None:
    def boom(_texts: list[str]) -> list[list[float]]:
        raise EmbeddingAuthError("OPENROUTER_API_KEY is not configured.")

    monkeypatch.setattr("jebaerme.services.embeddings.embed_texts", boom)
    response = client.post("/documents/search", json={"question": "x"})
    assert response.status_code == 502
    assert response.json() == {"detail": "OPENROUTER_API_KEY is not configured."}
