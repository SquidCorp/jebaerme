from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from jebaerme.api.app import create_app
from jebaerme.graphdb.graphdb import init_graph
from jebaerme.models.env import Settings


def test_init_graph_selects_named_graph(monkeypatch: MonkeyPatch) -> None:
    fake_graph = MagicMock()
    fake_db = MagicMock()
    fake_db.select_graph.return_value = fake_graph
    fake_ctor = MagicMock(return_value=fake_db)
    monkeypatch.setattr("jebaerme.graphdb.graphdb.FalkorDB", fake_ctor)

    graph = init_graph(
        host="127.0.0.1",
        port=6380,
        password="secret",
        username="default",
        graph_name="jobs",
    )

    fake_ctor.assert_called_once_with(
        host="127.0.0.1",
        port=6380,
        password="secret",
        username="default",
    )
    fake_db.select_graph.assert_called_once_with("jobs")
    fake_graph.query.assert_called_once_with("RETURN 1")
    assert graph is fake_graph


def test_init_graph_uses_settings_defaults(monkeypatch: MonkeyPatch) -> None:
    fake_graph = MagicMock()
    fake_db = MagicMock()
    fake_db.select_graph.return_value = fake_graph
    fake_ctor = MagicMock(return_value=fake_db)
    monkeypatch.setattr("jebaerme.graphdb.graphdb.FalkorDB", fake_ctor)
    settings = Settings(
        FALKORDB_HOST="falkordb.local",
        FALKORDB_PORT=7000,
        FALKORDB_USERNAME="app",
        FALKORDB_PASSWORD="graph-pass",
        FALKORDB_GRAPH="career",
    )

    graph = init_graph(settings=settings)

    fake_ctor.assert_called_once_with(
        host="falkordb.local",
        port=7000,
        password="graph-pass",
        username="app",
    )
    fake_db.select_graph.assert_called_once_with("career")
    assert graph is fake_graph


def test_create_app_inits_graph(stub_init_graph: MagicMock) -> None:
    app = create_app()
    with TestClient(app):
        stub_init_graph.assert_called_once_with()
        assert app.state.graph is stub_init_graph.return_value
    stub_init_graph.return_value.client.close.assert_called_once_with()
