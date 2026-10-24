"""Jev schema."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

DEFAULT_JEV_MODEL = "typesafe/jev-1.14"


class JevConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str = Field(
        default=DEFAULT_JEV_MODEL, description="Typesafe ai model version"
    )


class NoulCriteria(BaseModel):
    model_config = ConfigDict(extra="forbid")

    true: str = Field(
        min_length=25, description="A sentence that would make a decision true."
    )
    false: str = Field(
        min_length=25, description="A sentence that would make a decision false."
    )


class NoulQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["noul"] = "noul"
    instructions: str = Field(min_length=1, description="The question to be answered.")
    criteria: NoulCriteria


class ScoreQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["score"] = "score"
    instructions: str = Field(min_length=1, description="The question to be answered.")
    criteria: list[str] = Field(min_length=1)


class ChoiceQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["choice"] = "choice"
    instructions: str = Field(min_length=1, description="The question to be answered.")
    criteria: dict[str, str] = Field(min_length=1)


JevQuestion = Annotated[
    NoulQuestion | ScoreQuestion | ChoiceQuestion,
    Field(discriminator="type"),
]


class BaseJevRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str = Field(
        default=DEFAULT_JEV_MODEL, description="Typesafe ai model version"
    )
    state: str = Field(min_length=1, description="The input to evaluate")
    questions: dict[str, JevQuestion]


class NoulAnswer(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["noul"]
    noul: float = Field(ge=0, le=1, description="Probability of yes.")


class ChoiceAnswer(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["choice"]
    choice: str = Field(description="Selected option name.")
    probabilities: dict[str, float]
    confidence: float = Field(ge=0, le=1)


class ScoreAnswer(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["score"]
    score: float = Field(description="Probability-weighted position on the scale.")
    probabilities: dict[str, float]
    legend: dict[str, str]
    confidence: float = Field(ge=0, le=1)


JevAnswer = Annotated[
    NoulAnswer | ChoiceAnswer | ScoreAnswer,
    Field(discriminator="type"),
]


class JevUsage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    input_tokens: int
    output_tokens: int
    cost: float | None = None


class BaseJevResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    answers: dict[str, JevAnswer]
    model: str
    usage: JevUsage
    id: str | None = None
    provider: str | None = None
