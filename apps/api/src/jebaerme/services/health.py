"""Health status. No HTTP/router details."""

from jebaerme.db.qdrant import QdrantClientLike, qdrant_is_ready
from jebaerme.models.env import env
from jebaerme.models.health import Health


def get_health(*, qdrant_client: QdrantClientLike | None = None) -> Health:
    ready = qdrant_client is not None and qdrant_is_ready(qdrant_client)
    return Health(status="ok", env=env.APP_ENV, qdrant="ok" if ready else "unavailable")
