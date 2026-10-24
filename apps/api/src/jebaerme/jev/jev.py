"""Reusable Jev wrapper."""

import requests
from pydantic import TypeAdapter

from jebaerme.models.env import env
from jebaerme.models.jev import (
    BaseJevRequest,
    BaseJevResponse,
    ChoiceQuestion,
    JevConfig,
    JevQuestion,
    NoulCriteria,
    NoulQuestion,
    ScoreQuestion,
)

DECISIONS_URL = "https://openrouter.ai/api/alpha/decisions"


class JevAuthError(RuntimeError):
    """The Decisions API rejected the configured API key."""


_QUESTIONS = TypeAdapter(dict[str, JevQuestion])
_QUESTION = TypeAdapter(JevQuestion)

type JevCriteria = NoulCriteria | list[str] | dict[str, str]


class Jev:
    """Builds a Jev request so callers pass state and questions, not request JSON."""

    def __init__(
        self,
        questions: dict[str, JevQuestion] | None = None,
        config: JevConfig | None = None,
    ) -> None:
        self._questions = _QUESTIONS.validate_python(questions or {})
        self._config = config if config is not None else JevConfig()

    def list_questions(self) -> dict[str, JevQuestion]:
        return dict(self._questions)

    def add_a_question(self, key: str, question: JevQuestion) -> None:
        if key in self._questions:
            raise ValueError(f"question {key!r} already exists")
        self._questions[key] = _QUESTION.validate_python(question)

    def remove_a_question_by_key(self, key: str) -> None:
        try:
            del self._questions[key]
        except KeyError:
            raise KeyError(f"question {key!r} does not exist") from None

    def list_criteria(self, question_key: str) -> JevCriteria:
        question = self._get_question(question_key)
        if isinstance(question, NoulQuestion):
            return question.criteria.model_copy()
        if isinstance(question, ScoreQuestion):
            return list(question.criteria)
        return dict(question.criteria)

    def add_a_criteria(self, question_key: str, key: str, value: str) -> None:
        question = self._get_question(question_key)
        if isinstance(question, ChoiceQuestion):
            if key in question.criteria:
                raise ValueError(f"criteria {key!r} already exists")
            self._set_question(
                question_key,
                question.model_copy(
                    update={"criteria": {**question.criteria, key: value}}
                ),
            )
            return
        if isinstance(question, NoulQuestion):
            if key not in ("true", "false"):
                raise ValueError("noul criteria keys must be 'true' or 'false'")
            self._set_question(
                question_key,
                question.model_copy(
                    update={
                        "criteria": question.criteria.model_copy(update={key: value})
                    }
                ),
            )
            return
        self._set_question(
            question_key,
            question.model_copy(update={"criteria": [*question.criteria, value]}),
        )

    def remove_a_criteria_by_key(self, question_key: str, key: str) -> None:
        question = self._get_question(question_key)
        if isinstance(question, ChoiceQuestion):
            if key not in question.criteria:
                raise KeyError(f"criteria {key!r} does not exist")
            if len(question.criteria) == 1:
                raise ValueError("choice criteria must have at least one entry")
            criteria = {
                name: text for name, text in question.criteria.items() if name != key
            }
            self._set_question(
                question_key, question.model_copy(update={"criteria": criteria})
            )
            return
        if isinstance(question, NoulQuestion):
            raise ValueError("noul criteria true/false cannot be removed")
        try:
            index = int(key)
        except ValueError:
            raise ValueError("score criteria keys must be integer indexes") from None
        if index < 0 or index >= len(question.criteria):
            raise KeyError(f"criteria {key!r} does not exist")
        if len(question.criteria) == 1:
            raise ValueError("score criteria must have at least one entry")
        criteria = [text for i, text in enumerate(question.criteria) if i != index]
        self._set_question(
            question_key, question.model_copy(update={"criteria": criteria})
        )

    def request(self, state: str) -> BaseJevRequest:
        return BaseJevRequest(
            model=self._config.model,
            state=state,
            questions=self._questions,
        )

    def send(self, state: str) -> BaseJevResponse:
        if not self._questions:
            raise ValueError("questions must not be empty")
        api_key = env.openrouter_api_key()
        if api_key is None:
            raise JevAuthError("OPENROUTER_API_KEY is not configured.")
        response = requests.post(
            DECISIONS_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=self.request(state).model_dump(),
            timeout=30,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            if response.status_code == 401:
                raise JevAuthError(
                    "OpenRouter rejected OPENROUTER_API_KEY (401)."
                ) from exc
            raise
        return BaseJevResponse.model_validate(response.json())

    def _get_question(
        self, question_key: str
    ) -> NoulQuestion | ScoreQuestion | ChoiceQuestion:
        try:
            return self._questions[question_key]
        except KeyError:
            raise KeyError(f"question {question_key!r} does not exist") from None

    def _set_question(
        self, question_key: str, question: NoulQuestion | ScoreQuestion | ChoiceQuestion
    ) -> None:
        self._questions[question_key] = question
