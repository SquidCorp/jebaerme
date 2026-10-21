"""FastAPI application factory."""

from fastapi import FastAPI

from jebaerme.api.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(title="jebaerme")
    app.include_router(health_router)
    return app


app = create_app()
