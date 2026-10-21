"""Business rules. No HTTP/router details, no SQL strings."""

from jebaerme.models import Health
from jebaerme.models.env import env


def get_health() -> Health:
    return Health(status="ok", env=env.APP_ENV)
