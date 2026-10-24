from unittest.mock import MagicMock, patch

import pytest
import requests

from jebaerme.jev.jev import Jev, JevAuthError
from jebaerme.models.jev import (
    BaseJevRequest,
    ChoiceAnswer,
    ChoiceQuestion,
    JevConfig,
    NoulAnswer,
    NoulCriteria,
    NoulQuestion,
    ScoreAnswer,
    ScoreQuestion,
)


def test_noul_example() -> None:
    request = BaseJevRequest.model_validate(
        {
            "model": "typesafe/jev-1.14",
            "state": (
                "Task: clean up inactive accounts before the quarterly report.\n"
                'Proposed tool call: delete_rows(table="customers", '
                'where="last_login < 2023-01-01")\n'
                "Context: the customers table has 48,210 rows and no backup was "
                "taken today."
            ),
            "questions": {
                "safe_to_run": {
                    "type": "noul",
                    "instructions": (
                        "Is this action safe to run without a human approving it first?"
                    ),
                    "criteria": {
                        "true": (
                            "Reversible or low-impact, and clearly within the "
                            "stated task."
                        ),
                        "false": (
                            "Destructive, irreversible, or broader than the "
                            "task requires."
                        ),
                    },
                }
            },
        }
    )
    question = request.questions["safe_to_run"]
    assert question.type == "noul"
    assert question.criteria.true.startswith("Reversible")


def test_choice_example() -> None:
    request = BaseJevRequest.model_validate(
        {
            "model": "typesafe/jev-1.14",
            "state": (
                "My payout has failed three days in a row and support chat keeps "
                "timing out. I need this fixed today."
            ),
            "questions": {
                "team": {
                    "type": "choice",
                    "instructions": "Which team should handle this message?",
                    "criteria": {
                        "billing": "Payments, payouts, invoices, refunds",
                        "technical": "Bugs, outages, integrations, API errors",
                        "sales": "Pricing, upgrades, new accounts",
                    },
                }
            },
        }
    )
    question = request.questions["team"]
    assert question.type == "choice"
    assert "billing" in question.criteria


def test_score_example() -> None:
    request = BaseJevRequest.model_validate(
        {
            "model": "typesafe/jev-1.14",
            "state": (
                "Subject: Pricing for 40 seats\n\n"
                "Hi, we trialed your product last month across two teams and the "
                "engineers want to standardize on it.\n"
                "Our current contract with the incumbent ends on the 30th. Can you "
                "send enterprise pricing for 40 seats\n"
                "and let me know if you can do a security review call this week?"
            ),
            "questions": {
                "buying_intent": {
                    "type": "score",
                    "instructions": "How ready is this lead to buy?",
                    "criteria": [
                        "Just browsing, no stated need or timeline",
                        "Evaluating, comparing options without a deadline",
                        "Ready to buy, has budget and a clear need",
                        "Urgent, has a hard deadline and is asking to transact",
                    ],
                }
            },
        }
    )
    question = request.questions["buying_intent"]
    assert question.type == "score"
    assert len(question.criteria) == 4


def test_jev_builds_request_from_question_models() -> None:
    jev = Jev(
        {
            "safe_to_run": NoulQuestion(
                instructions=(
                    "Is this action safe to run without a human approving it first?"
                ),
                criteria=NoulCriteria(
                    true=(
                        "Reversible or low-impact, and clearly within the stated task."
                    ),
                    false=(
                        "Destructive, irreversible, or broader than the task requires."
                    ),
                ),
            )
        }
    )
    request = jev.request(
        "Task: clean up inactive accounts before the quarterly report."
    )
    assert request.model == "typesafe/jev-1.14"
    assert "safe_to_run" in request.questions
    assert request.questions["safe_to_run"].type == "noul"


def test_jev_uses_config_model() -> None:
    jev = Jev(
        {
            "team": ChoiceQuestion(
                instructions="Which team should handle this message?",
                criteria={
                    "billing": "Payments, payouts, invoices, refunds",
                    "technical": "Bugs, outages, integrations, API errors",
                    "sales": "Pricing, upgrades, new accounts",
                },
            )
        },
        JevConfig(model="typesafe/jev-1.14"),
    )
    request = jev.request(
        "My payout has failed three days in a row and support chat keeps timing out."
    )
    question = request.questions["team"]
    assert request.model == "typesafe/jev-1.14"
    assert question.type == "choice"
    assert "billing" in question.criteria


def test_jev_manages_questions() -> None:
    jev = Jev()
    question = ChoiceQuestion(
        instructions="Which team should handle this message?",
        criteria={"billing": "Payments, payouts, invoices, refunds"},
    )
    jev.add_a_question("team", question)
    assert list(jev.list_questions()) == ["team"]
    jev.remove_a_question_by_key("team")
    assert jev.list_questions() == {}
    with pytest.raises(KeyError, match="team"):
        jev.remove_a_question_by_key("team")


def test_jev_manages_choice_criteria() -> None:
    jev = Jev(
        {
            "team": ChoiceQuestion(
                instructions="Which team should handle this message?",
                criteria={"billing": "Payments, payouts, invoices, refunds"},
            )
        }
    )
    jev.add_a_criteria("team", "sales", "Pricing, upgrades, new accounts")
    criteria = jev.list_criteria("team")
    assert criteria == {
        "billing": "Payments, payouts, invoices, refunds",
        "sales": "Pricing, upgrades, new accounts",
    }
    jev.remove_a_criteria_by_key("team", "billing")
    assert jev.list_criteria("team") == {"sales": "Pricing, upgrades, new accounts"}


def test_jev_noul_criteria_can_be_replaced_not_removed() -> None:
    jev = Jev(
        {
            "safe_to_run": NoulQuestion(
                instructions=(
                    "Is this action safe to run without a human approving it first?"
                ),
                criteria=NoulCriteria(
                    true=(
                        "Reversible or low-impact, and clearly within the stated task."
                    ),
                    false=(
                        "Destructive, irreversible, or broader than the task requires."
                    ),
                ),
            )
        }
    )
    replacement = "Clearly reversible, scoped to the task, and easy to undo later."
    jev.add_a_criteria("safe_to_run", "true", replacement)
    criteria = jev.list_criteria("safe_to_run")
    assert isinstance(criteria, NoulCriteria)
    assert criteria.true == replacement
    with pytest.raises(ValueError, match="cannot be removed"):
        jev.remove_a_criteria_by_key("safe_to_run", "true")


def test_jev_manages_score_criteria_by_index() -> None:
    jev = Jev(
        {
            "buying_intent": ScoreQuestion(
                instructions="How ready is this lead to buy?",
                criteria=[
                    "Just browsing, no stated need or timeline",
                    "Evaluating, comparing options without a deadline",
                ],
            )
        }
    )
    jev.add_a_criteria(
        "buying_intent",
        "2",
        "Ready to buy, has budget and a clear need",
    )
    assert jev.list_criteria("buying_intent") == [
        "Just browsing, no stated need or timeline",
        "Evaluating, comparing options without a deadline",
        "Ready to buy, has budget and a clear need",
    ]
    jev.remove_a_criteria_by_key("buying_intent", "0")
    assert jev.list_criteria("buying_intent") == [
        "Evaluating, comparing options without a deadline",
        "Ready to buy, has budget and a clear need",
    ]


def _noul_jev() -> Jev:
    return Jev(
        {
            "safe_to_run": NoulQuestion(
                instructions=(
                    "Is this action safe to run without a human approving it first?"
                ),
                criteria=NoulCriteria(
                    true=(
                        "Reversible or low-impact, and clearly within the stated task."
                    ),
                    false=(
                        "Destructive, irreversible, or broader than the task requires."
                    ),
                ),
            )
        }
    )


@patch("jebaerme.jev.jev.requests.post")
@patch("jebaerme.jev.jev.env")
def test_jev_send_posts_decisions_request(
    mock_env: MagicMock, mock_post: MagicMock
) -> None:
    mock_env.openrouter_api_key.return_value = "test-key"
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "id": "gen-dec-1",
        "model": "typesafe/jev-1.14",
        "provider": "TypeSafe",
        "answers": {
            "safe_to_run": {"type": "noul", "noul": 0.12},
            "team": {
                "type": "choice",
                "choice": "billing",
                "confidence": 0.8,
                "probabilities": {"billing": 0.8, "technical": 0.2},
            },
            "buying_intent": {
                "type": "score",
                "score": 1.99,
                "confidence": 0.99,
                "probabilities": {"0": 0.0, "1": 0.01, "2": 0.99},
                "legend": {
                    "0": "Just browsing, no stated need or timeline",
                    "1": "Evaluating, comparing options without a deadline",
                    "2": "Ready to buy, has budget and a clear need",
                },
            },
        },
        "usage": {"input_tokens": 100, "output_tokens": 10, "cost": 0.0001},
    }
    result = _noul_jev().send("Task: clean up inactive accounts.")
    mock_post.assert_called_once()
    assert mock_post.call_args.args[0] == "https://openrouter.ai/api/alpha/decisions"
    assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Bearer test-key"
    assert mock_post.call_args.kwargs["json"]["state"] == (
        "Task: clean up inactive accounts."
    )
    noul = result.answers["safe_to_run"]
    choice = result.answers["team"]
    score = result.answers["buying_intent"]
    assert isinstance(noul, NoulAnswer)
    assert noul.noul == 0.12
    assert isinstance(choice, ChoiceAnswer)
    assert choice.choice == "billing"
    assert isinstance(score, ScoreAnswer)
    assert score.score == 1.99


@patch("jebaerme.jev.jev.env")
def test_jev_send_requires_api_key(mock_env: MagicMock) -> None:
    mock_env.openrouter_api_key.return_value = None
    with pytest.raises(JevAuthError, match="not configured"):
        _noul_jev().send("Task: clean up inactive accounts.")


@patch("jebaerme.jev.jev.requests.post")
@patch("jebaerme.jev.jev.env")
def test_jev_send_maps_401(mock_env: MagicMock, mock_post: MagicMock) -> None:
    mock_env.openrouter_api_key.return_value = "bad-key"
    mock_post.return_value.status_code = 401
    mock_post.return_value.raise_for_status.side_effect = requests.HTTPError("401")
    with pytest.raises(JevAuthError, match="401"):
        _noul_jev().send("Task: clean up inactive accounts.")
