"""Job business rules. No HTTP/router details, no SQL strings."""

import secrets

from sqlmodel import Session

from jebaerme.agents.agent import LlmAuthError
from jebaerme.agents.job_ad_scout import JobAdScout, JobAdScoutError
from jebaerme.db.job import Job, PersistenceConflictError
from jebaerme.db.job import delete as delete_job_row
from jebaerme.db.job import get_by_ad_url as get_job_row_by_ad_url
from jebaerme.db.job import get_by_id as get_job_row
from jebaerme.db.job import insert as insert_job_row
from jebaerme.db.job import list_all as list_job_rows
from jebaerme.db.job import update as update_job_row
from jebaerme.models.job import JobAdUrlCreate, JobCreate, JobPublic, JobUpdate

__all__ = [
    "JobAdScoutError",
    "JobConflictError",
    "JobNotFoundError",
    "LlmAuthError",
    "create_job",
    "create_job_from_url",
    "delete_job",
    "get_job",
    "list_jobs",
    "update_job",
]


class JobNotFoundError(Exception):
    """Raised when a job id does not exist."""


class JobConflictError(Exception):
    """Raised when a job uniqueness constraint fails."""


def create_job(session: Session, payload: JobCreate) -> JobPublic:
    job = Job(
        **payload.model_dump(),
        invitation_code=_new_invitation_code(),
    )
    try:
        saved = insert_job_row(session, job)
    except PersistenceConflictError as exc:
        raise JobConflictError(
            "A job with this ad URL or invitation code already exists."
        ) from exc
    return JobPublic.model_validate(saved)


def create_job_from_url(session: Session, payload: JobAdUrlCreate) -> JobPublic:
    ad_url = str(payload.ad_url)
    if get_job_row_by_ad_url(session, ad_url) is not None:
        raise JobConflictError(
            "A job with this ad URL or invitation code already exists."
        )
    return JobAdScout(persist=lambda job: create_job(session, job)).run(ad_url)


def get_job(session: Session, job_id: str) -> JobPublic:
    job = get_job_row(session, job_id)
    if job is None:
        raise JobNotFoundError(f"Job {job_id} was not found.")
    return JobPublic.model_validate(job)


def list_jobs(
    session: Session,
    *,
    offset: int = 0,
    limit: int = 100,
) -> list[JobPublic]:
    return [
        JobPublic.model_validate(job)
        for job in list_job_rows(session, offset=offset, limit=limit)
    ]


def update_job(session: Session, job_id: str, payload: JobUpdate) -> JobPublic:
    job = get_job_row(session, job_id)
    if job is None:
        raise JobNotFoundError(f"Job {job_id} was not found.")
    try:
        saved = update_job_row(session, job, payload.model_dump(exclude_unset=True))
    except PersistenceConflictError as exc:
        raise JobConflictError(
            "A job with this ad URL or invitation code already exists."
        ) from exc
    return JobPublic.model_validate(saved)


def delete_job(session: Session, job_id: str) -> None:
    job = get_job_row(session, job_id)
    if job is None:
        raise JobNotFoundError(f"Job {job_id} was not found.")
    delete_job_row(session, job)


def _new_invitation_code() -> str:
    return secrets.token_urlsafe(24)
