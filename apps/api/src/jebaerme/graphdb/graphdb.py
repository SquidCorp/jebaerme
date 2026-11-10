"""FalkorDB graph connection."""

from falkordb import FalkorDB, Graph

from jebaerme.models.env import Settings, env


def init_graph(
    *,
    host: str | None = None,
    port: int | None = None,
    password: str | None = None,
    username: str | None = None,
    graph_name: str | None = None,
    settings: Settings | None = None,
) -> Graph:
    """Connect to FalkorDB and create the named graph if it does not exist."""
    config = settings or env
    db = FalkorDB(
        host=host or config.FALKORDB_HOST,
        port=port if port is not None else config.FALKORDB_PORT,
        password=password if password is not None else config.falkordb_password(),
        username=username if username is not None else config.FALKORDB_USERNAME,
    )
    graph = db.select_graph(graph_name or config.FALKORDB_GRAPH)
    graph.query("RETURN 1")
    return graph
