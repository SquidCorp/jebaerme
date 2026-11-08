"""Firecrawl scrape API schemas."""

from pydantic import BaseModel, ConfigDict, Field


class FirecrawlMarkdownData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    markdown: str | None = Field(default=None, description="Scraped page as markdown.")


class FirecrawlScrapeResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    success: bool = Field(default=False, description="Whether the scrape succeeded.")
    data: FirecrawlMarkdownData | None = Field(
        default=None, description="Scrape payload."
    )
    error: str | None = Field(default=None, description="Provider error message.")
