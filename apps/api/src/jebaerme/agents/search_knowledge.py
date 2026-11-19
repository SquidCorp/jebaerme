"""Shared knowledge-base search tool for chat agents."""

from langchain.tools import tool

from jebaerme.db.qdrant import create_qdrant_client
from jebaerme.models.document import DocumentSearch
from jebaerme.services.documents import CollectionConfigError, search_documents
from jebaerme.services.embeddings import EmbeddingAuthError, EmbeddingError

NO_MATCHING_DOCUMENTS = "NO_MATCHING_DOCUMENTS"


@tool
def search_knowledge(query: str) -> str:
    """Search the knowledge base for passages that answer the user's question.

    Call this before answering. Derive a focused query from the user question.
    If this returns NO_MATCHING_DOCUMENTS, you must not invent facts.

    Args:
        query: Search query to embed and match against stored document chunks.
    """
    stripped = query.strip()
    if not stripped:
        return NO_MATCHING_DOCUMENTS
    try:
        client = create_qdrant_client()
        result = search_documents(client, DocumentSearch(question=stripped))
    except EmbeddingAuthError, EmbeddingError, CollectionConfigError:
        return NO_MATCHING_DOCUMENTS
    except Exception:
        return NO_MATCHING_DOCUMENTS
    if not result.hits:
        return NO_MATCHING_DOCUMENTS
    return "\n\n".join(
        (
            f"title={hit.title}\n"
            f"source={hit.source}\n"
            f"domain={hit.domain}\n"
            f"score={hit.score:.4f}\n"
            f"{hit.text}"
        )
        for hit in result.hits
    )
