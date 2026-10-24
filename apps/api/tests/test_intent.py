from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from jebaerme.api.app import create_app
from jebaerme.models.jev import BaseJevResponse, ChoiceAnswer, ChoiceQuestion
from jebaerme.services.intent import JevAuthError, classify_intent

_INTENT_RESPONSE = {
    "id": "gen-dec-1",
    "model": "typesafe/jev-1.14",
    "provider": "TypeSafe",
    "answers": {
        "intent": {
            "type": "choice",
            "choice": "soft_skills",
            "confidence": 0.8,
            "probabilities": {
                "generic": 0.1,
                "soft_skills": 0.8,
                "technical_skills": 0.1,
            },
        }
    },
    "usage": {"input_tokens": 100, "output_tokens": 10, "cost": 0.0001},
}


@patch("jebaerme.services.intent.Jev")
def test_classify_intent_sends_choice_question(mock_jev_cls: MagicMock) -> None:
    mock_jev_cls.return_value.send.return_value = BaseJevResponse.model_validate(
        _INTENT_RESPONSE
    )
    result = classify_intent("How does she handle conflict on a team?")
    questions = mock_jev_cls.call_args.args[0]
    question = questions["intent"]
    assert isinstance(question, ChoiceQuestion)
    assert question.instructions == "What is the intent of this message?"
    assert question.criteria == {
        "generic": (
            "intent is to learn something more personal about the person."
            "Personal details. Language spoken. Hobbies."
        ),
        "soft_skills": (
            "intent is about evaluating how the person acts in a "
            "professional environment. Will the person fit in the team."
        ),
        "technical_skills": (
            "intent is about evaluation the knowledge of the person in technical fields"
        ),
    }
    mock_jev_cls.return_value.send.assert_called_once_with(
        "How does she handle conflict on a team?"
    )
    answer = result.answers["intent"]
    assert isinstance(answer, ChoiceAnswer)
    assert answer.choice == "soft_skills"


@patch("jebaerme.api.decisions.classify_intent")
def test_intent_endpoint_returns_jev_response(classify: MagicMock) -> None:
    classify.return_value = BaseJevResponse.model_validate(_INTENT_RESPONSE)
    client = TestClient(create_app())
    response = client.post(
        "/decisions/intent",
        json={"state": "How does she handle conflict on a team?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["answers"]["intent"]["choice"] == "soft_skills"
    classify.assert_called_once_with("How does she handle conflict on a team?")


@patch("jebaerme.api.decisions.classify_intent", side_effect=JevAuthError("rejected"))
def test_intent_endpoint_maps_auth_error(_classify: MagicMock) -> None:
    client = TestClient(create_app())
    response = client.post("/decisions/intent", json={"state": "Tell me about Alice"})
    assert response.status_code == 502
    assert response.json() == {"detail": "rejected"}


def test_intent_endpoint_rejects_empty_state() -> None:
    client = TestClient(create_app())
    response = client.post("/decisions/intent", json={"state": ""})
    assert response.status_code == 422
