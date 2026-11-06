"""Jobs HTTP adapters."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlmodel import Session

from jebaerme.db.session import get_session
from jebaerme.models.job import JobAdUrlCreate, JobCreate, JobPublic, JobUpdate
from jebaerme.services.jobs import (
    JobAdScoutError,
    JobConflictError,
    JobNotFoundError,
    LlmAuthError,
    create_job,
    create_job_from_url,
    delete_job,
    get_job,
    list_jobs,
    update_job,
)

router = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]


@router.post("/jobs", response_model=JobPublic, status_code=201)
def jobs_create(body: JobCreate, session: SessionDep) -> JobPublic:
    try:
        return create_job(session, body)
    except JobConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/jobs/new/url", response_model=JobPublic, status_code=201)
def jobs_create_from_url(body: JobAdUrlCreate, session: SessionDep) -> JobPublic:
    try:
        return create_job_from_url(session, body)
    except JobConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except LlmAuthError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except JobAdScoutError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/jobs", response_model=list[JobPublic])
def jobs_list(
    session: SessionDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[JobPublic]:
    return list_jobs(session, offset=offset, limit=limit)


@router.get("/jobs/{job_id}", response_model=JobPublic)
def jobs_get(job_id: str, session: SessionDep) -> JobPublic:
    try:
        return get_job(session, job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/jobs/{job_id}", response_model=JobPublic)
def jobs_update(job_id: str, body: JobUpdate, session: SessionDep) -> JobPublic:
    try:
        return update_job(session, job_id, body)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except JobConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/jobs/{job_id}", status_code=204)
def jobs_delete(job_id: str, session: SessionDep) -> Response:
    try:
        delete_job(session, job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=204)
