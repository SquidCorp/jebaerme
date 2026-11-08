from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests
from pydantic import SecretStr
from sqlmodel import Session

from jebaerme.agents.job_ad_scout import JobAdScout, JobAdScoutError, fetch_job_ad_page
from jebaerme.db.session import create_db_engine, init_db
from jebaerme.models.job import JobCreate, JobPublic
from jebaerme.services.jobs import create_job, get_job


@pytest.fixture
def session(tmp_path: Path) -> Iterator[Session]:
    engine = create_db_engine(f"sqlite:///{tmp_path / 'scout.db'}")
    init_db(engine)
    with Session(engine) as db_session:
        yield db_session
    engine.dispose()


def _scrape_response(*, markdown: str, success: bool = True) -> MagicMock:
    response = MagicMock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = {
        "success": success,
        "data": {"markdown": markdown},
    }
    return response


@pytest.fixture
def firecrawl_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "jebaerme.agents.job_ad_scout.env.FIRECRAWL_API_KEY",
        SecretStr("fc-test"),
    )


@patch("jebaerme.agents.job_ad_scout.requests.post")
def test_fetch_job_ad_page_returns_markdown(
    mock_post: MagicMock, firecrawl_key: None
) -> None:
    mock_post.return_value = _scrape_response(markdown="# Staff Engineer\n\nParis")
    assert "Staff Engineer" in fetch_job_ad_page("https://jobs.example.com/ad")
    mock_post.assert_called_once()
    assert mock_post.call_args.args[0] == "https://api.firecrawl.dev/v2/scrape"
    assert mock_post.call_args.kwargs["timeout"] == 30
    assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Bearer fc-test"
    assert mock_post.call_args.kwargs["json"] == {
        "url": "https://jobs.example.com/ad",
        "onlyMainContent": True,
        "maxAge": 172800000,
        "parsers": ["pdf"],
        "formats": ["markdown"],
    }


@patch("jebaerme.agents.job_ad_scout.requests.post")
def test_fetch_job_ad_page_http_error(
    mock_post: MagicMock, firecrawl_key: None
) -> None:
    mock_post.return_value.ok = False
    mock_post.return_value.status_code = 401
    assert "HTTP 401" in fetch_job_ad_page("https://jobs.example.com/ad")


@patch("jebaerme.agents.job_ad_scout.requests.post")
def test_fetch_job_ad_page_truncates_markdown(
    mock_post: MagicMock, firecrawl_key: None
) -> None:
    mock_post.return_value = _scrape_response(markdown="x" * 40_000)
    text = fetch_job_ad_page("https://jobs.example.com/ad")
    assert text.endswith("[truncated]")
    assert len(text) < 40_000


@patch("jebaerme.agents.job_ad_scout.requests.post")
def test_fetch_job_ad_page_request_error(
    mock_post: MagicMock, firecrawl_key: None
) -> None:
    mock_post.side_effect = requests.RequestException("timeout")
    assert fetch_job_ad_page("https://jobs.example.com/ad").startswith(
        "Failed to fetch URL:"
    )


@patch("jebaerme.agents.job_ad_scout.requests.post")
def test_fetch_job_ad_page_scrape_error(
    mock_post: MagicMock, firecrawl_key: None
) -> None:
    mock_post.return_value = _scrape_response(markdown="", success=False)
    mock_post.return_value.json.return_value = {
        "success": False,
        "error": "blocked",
    }
    assert "blocked" in fetch_job_ad_page("https://jobs.example.com/ad")


def test_fetch_job_ad_page_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "jebaerme.agents.job_ad_scout.env.FIRECRAWL_API_KEY",
        None,
    )
    assert fetch_job_ad_page("https://jobs.example.com/ad") == (
        "Failed to fetch URL: FIRECRAWL_API_KEY is not set."
    )


@patch("jebaerme.agents.job_ad_scout.DeepAgent")
def test_run_requires_save(mock_agent_cls: MagicMock) -> None:
    mock_agent_cls.return_value.invoke.return_value = "done"
    persist = MagicMock()
    with pytest.raises(JobAdScoutError, match="did not save"):
        JobAdScout(persist=persist).run("https://jobs.example.com/ad")
    persist.assert_not_called()


@patch("jebaerme.agents.job_ad_scout.DeepAgent")
def test_run_saves_extracted_job(mock_agent_cls: MagicMock, session: Session) -> None:
    ad_url = "https://jobs.example.com/acme-engineer"

    def invoke_save(_msg: str) -> str:
        tools = mock_agent_cls.call_args.kwargs["tools"]
        save_tool = next(tool for tool in tools if tool.name == "save_job")
        return str(
            save_tool.invoke(
                {
                    "company_name": "Acme",
                    "job_title": "Engineer",
                    "full_remote": True,
                    "location": "Paris",
                }
            )
        )

    mock_agent_cls.return_value.invoke.side_effect = invoke_save
    job = JobAdScout(persist=lambda payload: create_job(session, payload)).run(ad_url)
    loaded = get_job(session, job.id)
    assert loaded.ad_url == ad_url
    assert loaded.company_name == "Acme"
    assert loaded.job_title == "Engineer"
    assert loaded.full_remote is True
    assert loaded.location == "Paris"
    assert loaded.markdown is None


@patch("jebaerme.agents.job_ad_scout.requests.post")
@patch("jebaerme.agents.job_ad_scout.DeepAgent")
def test_run_saves_fetched_markdown(
    mock_agent_cls: MagicMock,
    mock_post: MagicMock,
    session: Session,
    firecrawl_key: None,
) -> None:
    ad_url = "https://jobs.example.com/acme-engineer"
    markdown = "# Staff Engineer\n\nParis"
    mock_post.return_value = _scrape_response(markdown=markdown)

    def invoke_fetch_then_save(_msg: str) -> str:
        tools = mock_agent_cls.call_args.kwargs["tools"]
        fetch_tool = next(tool for tool in tools if tool.name == "fetch_job_ad")
        save_tool = next(tool for tool in tools if tool.name == "save_job")
        fetch_tool.invoke({"url": ad_url})
        return str(
            save_tool.invoke(
                {
                    "company_name": "Acme",
                    "job_title": "Engineer",
                    "full_remote": True,
                    "location": "Paris",
                }
            )
        )

    mock_agent_cls.return_value.invoke.side_effect = invoke_fetch_then_save
    job = JobAdScout(persist=lambda payload: create_job(session, payload)).run(ad_url)
    loaded = get_job(session, job.id)
    assert loaded.markdown == markdown


@patch("jebaerme.agents.job_ad_scout.DeepAgent")
def test_fetch_tool_refuses_other_urls(mock_agent_cls: MagicMock) -> None:
    results: list[str] = []

    def invoke_fetch(_msg: str) -> str:
        tools = mock_agent_cls.call_args.kwargs["tools"]
        fetch_tool = next(tool for tool in tools if tool.name == "fetch_job_ad")
        results.append(str(fetch_tool.invoke({"url": "https://evil.example/"})))
        return results[-1]

    mock_agent_cls.return_value.invoke.side_effect = invoke_fetch
    with pytest.raises(JobAdScoutError):
        JobAdScout(persist=_unused_persist).run("https://jobs.example.com/ad")
    assert "Refusing" in results[0]


def _unused_persist(payload: JobCreate) -> JobPublic:
    raise AssertionError(f"unexpected persist: {payload}")
