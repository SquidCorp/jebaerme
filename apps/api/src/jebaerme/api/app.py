"""FastAPI application factory."""

from collections.abc import AsyncGenerator, Iterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import Session

from jebaerme.api.chat import router as chat_router
from jebaerme.api.decisions import router as decisions_router
from jebaerme.api.health import router as health_router
from jebaerme.api.jobs import router as jobs_router
from jebaerme.db.session import create_db_engine, get_session, init_db


def create_app(*, database_url: str | None = None) -> FastAPI:
    engine = create_db_engine(database_url)

    def session_override() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
        init_db(engine)
        yield
        engine.dispose()

    app = FastAPI(title="jebaerme", lifespan=lifespan)
    app.dependency_overrides[get_session] = session_override
    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(decisions_router)
    app.include_router(jobs_router)
    return app


app = create_app()
