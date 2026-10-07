from jebaerme.services import get_health


def test_health_status_ok() -> None:
    health = get_health()
    assert health.status == "ok"
