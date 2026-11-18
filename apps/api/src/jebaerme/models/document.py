"""Document ingest request and response schemas. No I/O."""

from pathlib import PurePosixPath
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

DocumentSource = Literal["cv", "projects", "experiences", "eval_reports"]
DocumentDomain = Literal["business", "technical", "general"]
DocumentSourceKind = Literal["markdown", "url", "file"]


class DocumentIngest(BaseModel):
    title: str = Field(min_length=1)
    text: str
    source: DocumentSource
    source_kind: DocumentSourceKind = "markdown"
    url: str | None = None
    domain: DocumentDomain = "general"
    tags: list[str] = Field(default_factory=list)
    language: str = Field(default="en", min_length=1)
    source_priority: int = Field(default=50, ge=0, le=100)
    source_ids: list[str] = Field(default_factory=list)
    document_id: str | None = None

    @field_validator("text")
    @classmethod
    def strip_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("text must not be empty")
        return stripped

    @field_validator("tags")
    @classmethod
    def drop_empty_tags(cls, value: list[str]) -> list[str]:
        return [tag for tag in value if tag]

    @field_validator("source_ids")
    @classmethod
    def validate_source_ids(cls, value: list[str]) -> list[str]:
        for item in value:
            if (
                not item
                or "\\" in item
                or item.startswith("/")
                or ".." in PurePosixPath(item).parts
            ):
                raise ValueError(
                    "source_ids must be relative POSIX paths without empty, "
                    "absolute, or parent segments"
                )
        return value

    @model_validator(mode="after")
    def url_required_for_url_kind(self) -> DocumentIngest:
        if self.source_kind == "url" and not self.url:
            raise ValueError("url is required when source_kind is url")
        return self


class DocumentIngestPublic(BaseModel):
    document_id: str
    title: str
    source: DocumentSource
    domain: DocumentDomain
    source_priority: int
    chunk_count: int
    skipped_chunks: int
    point_ids: list[str]
