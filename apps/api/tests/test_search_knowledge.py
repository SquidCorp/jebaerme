from unittest.mock import MagicMock, patch

from jebaerme.agents.search_knowledge import NO_MATCHING_DOCUMENTS, search_knowledge
from jebaerme.models.document import (
    DocumentSearch,
    DocumentSearchHit,
    DocumentSearchPublic,
)
from jebaerme.services.embeddings import EmbeddingAuthError


@patch("jebaerme.agents.search_knowledge.search_documents")
@patch("jebaerme.agents.search_knowledge.create_qdrant_client")
def test_empty_query_skips_search(
    _mock_client: MagicMock, mock_search: MagicMock
) -> None:
    assert search_knowledge.invoke({"query": ""}) == NO_MATCHING_DOCUMENTS
    assert search_knowledge.invoke({"query": "   "}) == NO_MATCHING_DOCUMENTS
    mock_search.assert_not_called()


@patch("jebaerme.agents.search_knowledge.search_documents")
@patch("jebaerme.agents.search_knowledge.create_qdrant_client")
def test_empty_hits_returns_no_matching_documents(
    _mock_client: MagicMock, mock_search: MagicMock
) -> None:
    mock_search.return_value = DocumentSearchPublic(hits=[])
    assert search_knowledge.invoke({"query": "alpha"}) == NO_MATCHING_DOCUMENTS


@patch("jebaerme.agents.search_knowledge.search_documents")
@patch("jebaerme.agents.search_knowledge.create_qdrant_client")
def test_formats_hit(_mock_client: MagicMock, mock_search: MagicMock) -> None:
    mock_search.return_value = DocumentSearchPublic(
        hits=[
            DocumentSearchHit(
                score=0.91,
                text="alpha knowledge",
                document_id="d1",
                title="Alpha CV",
                source="cv",
                domain="general",
                roles=[],
                chunk_index=0,
            )
        ]
    )
    body = search_knowledge.invoke({"query": "alpha"})
    assert "title=Alpha CV" in body
    assert "source=cv" in body
    assert "domain=general" in body
    assert "score=0.9100" in body
    assert "alpha knowledge" in body
    mock_search.assert_called_once()
    assert mock_search.call_args.args[1] == DocumentSearch(question="alpha")


@patch("jebaerme.agents.search_knowledge.search_documents")
@patch("jebaerme.agents.search_knowledge.create_qdrant_client")
def test_embedding_auth_error_returns_no_matching_documents(
    _mock_client: MagicMock, mock_search: MagicMock
) -> None:
    mock_search.side_effect = EmbeddingAuthError("nope")
    assert search_knowledge.invoke({"query": "alpha"}) == NO_MATCHING_DOCUMENTS
