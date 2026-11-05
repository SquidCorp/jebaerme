from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from jebaerme.api.app import create_app
from jebaerme.models.jev import BaseJevResponse, NoulAnswer, NoulQuestion
from jebaerme.services.topic import (
    JevAuthError,
    filter_out_topic,
    is_topic_allowed,
)

_TOPIC_RESPONSE = {
    "id": "gen-dec-2",
    "model": "typesafe/jev-1.14",
    "provider": "TypeSafe",
    "answers": {
        "filter_out": {
            "type": "noul",
            "noul": 0.92,
        }
    },
    "usage": {"input_tokens": 100, "output_tokens": 10, "cost": 0.0001},
}


@patch("jebaerme.services.topic.Jev")
def test_filter_out_topic_sends_noul_question(mock_jev_cls: MagicMock) -> None:
    mock_jev_cls.return_value.send.return_value = BaseJevResponse.model_validate(
        _TOPIC_RESPONSE
    )
    result = filter_out_topic("Tell me about your system design experience.")
    questions = mock_jev_cls.call_args.args[0]
    question = questions["filter_out"]
    assert isinstance(question, NoulQuestion)
    assert question.instructions == (
        "A HR or technical recruiter sends a message to evaluate a "
        "candidate during a job interview. But all messages should not "
        "trigger the system. Is this message safe to be processes?"
    )
    assert "job interview" in question.criteria.true
    assert "political views" in question.criteria.false
    mock_jev_cls.return_value.send.assert_called_once_with(
        "Tell me about your system design experience."
    )
    answer = result.answers["filter_out"]
    assert isinstance(answer, NoulAnswer)
    assert answer.noul == 0.92


def test_is_topic_allowed_uses_noul_threshold() -> None:
    allowed = BaseJevResponse.model_validate(_TOPIC_RESPONSE)
    blocked = BaseJevResponse.model_validate(
        {
            **_TOPIC_RESPONSE,
            "answers": {"filter_out": {"type": "noul", "noul": 0.1}},
        }
    )
    missing = BaseJevResponse.model_validate(
        {**_TOPIC_RESPONSE, "answers": {}},
    )
    assert is_topic_allowed(allowed) is True
    assert is_topic_allowed(blocked) is False
    assert is_topic_allowed(missing) is True


@patch("jebaerme.api.decisions.filter_out_topic")
def test_topic_endpoint_returns_jev_response(classify: MagicMock) -> None:
    classify.return_value = BaseJevResponse.model_validate(_TOPIC_RESPONSE)
    client = TestClient(create_app())
    response = client.post(
        "/decisions/topic",
        json={"state": "Tell me about your system design experience."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["answers"]["filter_out"]["noul"] == 0.92
    classify.assert_called_once_with("Tell me about your system design experience.")


@patch("jebaerme.api.decisions.filter_out_topic", side_effect=JevAuthError("rejected"))
def test_topic_endpoint_maps_auth_error(_classify: MagicMock) -> None:
    client = TestClient(create_app())
    response = client.post("/decisions/topic", json={"state": "What is your address?"})
    assert response.status_code == 502
    assert response.json() == {"detail": "rejected"}


def test_topic_endpoint_rejects_empty_state() -> None:
    client = TestClient(create_app())
    response = client.post("/decisions/topic", json={"state": ""})
    assert response.status_code == 422
