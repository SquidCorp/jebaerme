"""Job table and persistence operations."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlmodel import Field, Session, SQLModel, select


class PersistenceConflictError(Exception):
    """Raised when a uniqueness constraint fails."""


class Job(SQLModel, table=True):
    __tablename__ = "jobs"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    company_name: str
    ad_url: str = Field(unique=True, index=True)
    job_title: str
    full_remote: bool = Field(default=False)
    location: str | None = Field(default=None)
    invitation_code: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


def insert(session: Session, job: Job) -> Job:
    session.add(job)
    _commit(session)
    session.refresh(job)
    return job


def get_by_id(session: Session, job_id: str) -> Job | None:
    return session.get(Job, job_id)


def get_by_ad_url(session: Session, ad_url: str) -> Job | None:
    statement = select(Job).where(Job.ad_url == ad_url)
    return session.exec(statement).first()


def list_all(session: Session, *, offset: int = 0, limit: int = 100) -> list[Job]:
    statement = select(Job).offset(offset).limit(limit)
    return list(session.exec(statement).all())


def update(session: Session, job: Job, fields: dict[str, object]) -> Job:
    job.sqlmodel_update(fields)
    session.add(job)
    _commit(session)
    session.refresh(job)
    return job


def delete(session: Session, job: Job) -> None:
    session.delete(job)
    _commit(session)


def _commit(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise PersistenceConflictError from exc
