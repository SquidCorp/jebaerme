"""Engine, sessions, and schema creation."""

from collections.abc import Iterator
from pathlib import Path
from sqlite3 import Connection

from sqlalchemy.engine import Engine
from sqlalchemy.event import listen
from sqlmodel import Session, SQLModel, create_engine

from jebaerme.models.env import env


def create_db_engine(database_url: str | None = None) -> Engine:
    url = database_url or env.DATABASE_URL
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args)
    if url.startswith("sqlite"):
        listen(engine, "connect", _enable_sqlite_foreign_keys)
    return engine


def init_db(engine: Engine) -> None:
    database = engine.url.database
    if engine.url.drivername.startswith("sqlite") and database not in {
        None,
        ":memory:",
    }:
        Path(database).parent.mkdir(parents=True, exist_ok=True)

    from jebaerme.db.job import Job

    _ = Job
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    raise RuntimeError("Database session dependency is not configured")


def _enable_sqlite_foreign_keys(
    dbapi_connection: Connection,
    _connection_record: object,
) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
