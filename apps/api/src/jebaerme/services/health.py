"""Health status. No HTTP/router details."""

from jebaerme.models.env import env
from jebaerme.models.health import Health


def get_health() -> Health:
    return Health(status="ok", env=env.APP_ENV)
