"""Job ad scout: fetch a posting URL, extract fields, persist via callback."""

from collections.abc import Callable

import requests
from langchain.tools import tool
from langchain_core.tools import BaseTool

from jebaerme.agents.deepagent import DeepAgent
from jebaerme.models.agent import AgentConfig, AgentPrompt
from jebaerme.models.env import env
from jebaerme.models.firecrawl import FirecrawlScrapeResponse
from jebaerme.models.job import JobCreate, JobPublic

_FIRECRAWL_SCRAPE_URL = "https://api.firecrawl.dev/v2/scrape"
_FETCH_TIMEOUT_S = 30
_MAX_AD_CHARS = 32_000
_SYSTEM_PROMPT = """You are Job Ad Scout.

Fetch the job ad page, extract hiring facts, then save them.

1. Call fetch_job_ad with the user-provided URL.
2. Temporaly save the markdown content you get in a file. 
3. Read the page. Use edit_file tool to strip unrelated content: navigation, footers,
   cookie banners, related-job lists, and links to other internal
   or external pages. Keep only the job ad itself.
4. If it is not a job ad, or company_name or job_title cannot be
   determined, do not save.
5. Call save_job with:
   - company_name (required)
   - job_title (required)
   - full_remote: true only when the role is fully remote
   - location: city, region, or country when present; omit when unknown
   - markdown: the **EDITED** version
6. Do not invent facts.


The ad URL is bound by the save tool; you cannot change it."""


class JobAdScoutError(RuntimeError):
    """Raised when the scout does not persist a job."""


class JobAdScout:
    """Deep agent that reads a job ad URL and saves extracted fields."""

    def __init__(self, persist: Callable[[JobCreate], JobPublic]) -> None:
        self._persist = persist

    def run(self, ad_url: str) -> JobPublic:
        saved: list[JobPublic] = []
        agent = DeepAgent(
            AgentPrompt(prompt=_SYSTEM_PROMPT),
            AgentConfig(model=env.CHAT_MODEL, temperature=0),
            tools=_job_ad_tools(ad_url, self._persist, saved),
        )
        agent.invoke(f"Scout this job ad: {ad_url}")
        if not saved:
            raise JobAdScoutError("Job ad scout did not save a job.")
        return saved[-1]


def fetch_job_ad_page(url: str) -> str:
    api_key = env.firecrawl_api_key()
    if not api_key:
        return "Failed to fetch URL: FIRECRAWL_API_KEY is not set."
    try:
        response = requests.post(
            _FIRECRAWL_SCRAPE_URL,
            timeout=_FETCH_TIMEOUT_S,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "url": url,
                "onlyMainContent": True,
                "maxAge": 172800000,
                "parsers": ["pdf"],
                "formats": ["markdown"],
            },
        )
    except requests.RequestException as exc:
        return f"Failed to fetch URL: {exc}"
    if not response.ok:
        return f"Failed to fetch URL: HTTP {response.status_code}"
    try:
        payload = FirecrawlScrapeResponse.model_validate(response.json())
    except ValueError:
        return f"Failed to fetch URL: HTTP {response.status_code}"
    markdown = payload.data.markdown if payload.data is not None else None
    if not payload.success or not markdown:
        detail = payload.error or "Firecrawl returned no markdown."
        return f"Failed to fetch URL: {detail}"
    if len(markdown) > _MAX_AD_CHARS:
        return f"{markdown[:_MAX_AD_CHARS]}\n[truncated]"
    return markdown


def _job_ad_tools(
    ad_url: str,
    persist: Callable[[JobCreate], JobPublic],
    saved: list[JobPublic],
) -> list[BaseTool]:
    fetched_markdown: list[str] = []

    @tool
    def fetch_job_ad(url: str) -> str:
        """Download the job ad page for the URL the user posted.

        Args:
            url: Job ad URL posted by the user.
        """
        if url.rstrip("/") != ad_url.rstrip("/"):
            return f"Refusing to fetch {url}; only {ad_url} is allowed."
        page = fetch_job_ad_page(ad_url)
        if not page.startswith("Failed to fetch URL:"):
            fetched_markdown.clear()
            fetched_markdown.append(page)
        return page

    @tool
    def save_job(
        company_name: str,
        job_title: str,
        full_remote: bool = False,
        location: str | None = None,
        markdown: str | None = None,
    ) -> str:
        """Save extracted job ad fields to the jobs table.

        Args:
            company_name: Company that published the ad.
            job_title: Role title from the ad.
            full_remote: True only if the role is fully remote.
            location: City, region, or country, if present.
            markdown: Edited job ad markdown, if provided.
        """
        saved_markdown = markdown or (
            fetched_markdown[-1] if fetched_markdown else None
        )
        job = persist(
            JobCreate(
                company_name=company_name,
                ad_url=ad_url,
                job_title=job_title,
                full_remote=full_remote,
                location=location or None,
                markdown=saved_markdown,
            )
        )
        saved.append(job)
        return f"Saved job {job.id}"

    return [fetch_job_ad, save_job]
