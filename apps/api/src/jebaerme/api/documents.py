"""Documents HTTP adapters."""

from fastapi import APIRouter, HTTPException, Request
from qdrant_client import QdrantClient

from jebaerme.models.document import DocumentIngest, DocumentIngestPublic
from jebaerme.services.documents import (
    CollectionConfigError,
    DocumentIngestError,
    ingest_document,
)
from jebaerme.services.embeddings import EmbeddingAuthError, EmbeddingError

router = APIRouter()


@router.post("/documents", response_model=DocumentIngestPublic, status_code=201)
def documents_create(body: DocumentIngest, request: Request) -> DocumentIngestPublic:
    client = request.app.state.qdrant
    if not isinstance(client, QdrantClient):
        raise HTTPException(status_code=503, detail="Qdrant client is not available")
    try:
        return ingest_document(client, body)
    except DocumentIngestError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (EmbeddingAuthError, EmbeddingError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except CollectionConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
