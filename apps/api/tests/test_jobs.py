from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from jebaerme.api.app import create_app
from jebaerme.db.session import create_db_engine, init_db
from jebaerme.models.job import JobCreate, JobPublic, JobUpdate
from jebaerme.services.jobs import (
    JobAdScoutError,
    JobNotFoundError,
    LlmAuthError,
    create_job,
    get_job,
)


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    app = create_app(database_url=f"sqlite:///{tmp_path / 'test.db'}")
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def session(tmp_path: Path) -> Iterator[Session]:
    engine = create_db_engine(f"sqlite:///{tmp_path / 'service.db'}")
    init_db(engine)
    with Session(engine) as db_session:
        yield db_session
    engine.dispose()


def _job_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "company_name": "Acme",
        "ad_url": "https://jobs.example.com/acme-engineer",
        "job_title": "Engineer",
        "full_remote": True,
        "location": "Paris",
    }
    payload.update(overrides)
    return payload


def test_create_job_generates_server_fields(session: Session) -> None:
    job = create_job(session, JobCreate.model_validate(_job_payload()))
    assert job.company_name == "Acme"
    assert job.invitation_code
    assert job.id
    loaded = get_job(session, job.id)
    assert loaded.invitation_code == job.invitation_code


def test_create_job_invitation_code_is_32_chars(session: Session) -> None:
    job = create_job(session, JobCreate.model_validate(_job_payload()))
    assert len(job.invitation_code) == 32


def test_get_job_missing(session: Session) -> None:
    with pytest.raises(JobNotFoundError):
        get_job(session, "missing")


def test_create_and_get_job_endpoint(client: TestClient) -> None:
    created = client.post("/jobs", json=_job_payload())
    assert created.status_code == 201
    body = created.json()
    assert body["company_name"] == "Acme"
    assert body["full_remote"] is True
    assert body["invitation_code"]

    fetched = client.get(f"/jobs/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == body["id"]


def test_list_jobs_endpoint(client: TestClient) -> None:
    client.post("/jobs", json=_job_payload())
    client.post(
        "/jobs",
        json=_job_payload(
            company_name="Globex",
            ad_url="https://jobs.example.com/globex",
            job_title="Designer",
        ),
    )
    response = client.get("/jobs")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_update_job_endpoint(client: TestClient) -> None:
    created = client.post("/jobs", json=_job_payload()).json()
    response = client.patch(
        f"/jobs/{created['id']}", json={"job_title": "Staff Engineer"}
    )
    assert response.status_code == 200
    assert response.json()["job_title"] == "Staff Engineer"
    assert response.json()["company_name"] == "Acme"


def test_delete_job_endpoint(client: TestClient) -> None:
    created = client.post("/jobs", json=_job_payload()).json()
    deleted = client.delete(f"/jobs/{created['id']}")
    assert deleted.status_code == 204
    missing = client.get(f"/jobs/{created['id']}")
    assert missing.status_code == 404


def test_duplicate_ad_url_conflict(client: TestClient) -> None:
    first = client.post("/jobs", json=_job_payload())
    assert first.status_code == 201
    second = client.post("/jobs", json=_job_payload(job_title="Other"))
    assert second.status_code == 409


def test_missing_job_http_errors(client: TestClient) -> None:
    assert client.get("/jobs/missing").status_code == 404
    assert (
        client.patch("/jobs/missing", json=JobUpdate().model_dump()).status_code == 404
    )
    assert client.delete("/jobs/missing").status_code == 404


def test_create_job_validation_error(client: TestClient) -> None:
    response = client.post("/jobs", json={"company_name": "Acme"})
    assert response.status_code == 422


def _public_job(**overrides: object) -> JobPublic:
    payload: dict[str, object] = {
        "id": "job-1",
        "company_name": "Acme",
        "ad_url": "https://jobs.example.com/acme-engineer",
        "job_title": "Engineer",
        "full_remote": True,
        "location": "Paris",
        "invitation_code": "inv",
        "created_at": datetime.now(UTC),
    }
    payload.update(overrides)
    return JobPublic.model_validate(payload)


@patch("jebaerme.services.jobs.JobAdScout")
def test_create_from_url_endpoint(
    mock_scout_cls: MagicMock, client: TestClient
) -> None:
    mock_scout_cls.return_value.run.return_value = _public_job()
    response = client.post(
        "/jobs/new/url",
        json={"ad_url": "https://jobs.example.com/acme-engineer"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["job_title"] == "Engineer"
    assert body["ad_url"] == "https://jobs.example.com/acme-engineer"
    mock_scout_cls.return_value.run.assert_called_once_with(
        "https://jobs.example.com/acme-engineer"
    )


def test_create_from_url_rejects_invalid_url(client: TestClient) -> None:
    response = client.post("/jobs/new/url", json={"ad_url": "not-a-url"})
    assert response.status_code == 422


def test_create_from_url_duplicate_conflict(client: TestClient) -> None:
    created = client.post("/jobs", json=_job_payload())
    assert created.status_code == 201
    response = client.post(
        "/jobs/new/url",
        json={"ad_url": _job_payload()["ad_url"]},
    )
    assert response.status_code == 409


@patch("jebaerme.services.jobs.JobAdScout")
def test_create_from_url_maps_auth_error(
    mock_scout_cls: MagicMock, client: TestClient
) -> None:
    mock_scout_cls.return_value.run.side_effect = LlmAuthError("rejected")
    response = client.post(
        "/jobs/new/url",
        json={"ad_url": "https://jobs.example.com/acme-engineer"},
    )
    assert response.status_code == 502
    assert response.json() == {"detail": "rejected"}


@patch("jebaerme.services.jobs.JobAdScout")
def test_create_from_url_maps_scout_error(
    mock_scout_cls: MagicMock, client: TestClient
) -> None:
    mock_scout_cls.return_value.run.side_effect = JobAdScoutError(
        "Job ad scout did not save a job."
    )
    response = client.post(
        "/jobs/new/url",
        json={"ad_url": "https://jobs.example.com/ad"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Job ad scout did not save a job."}
