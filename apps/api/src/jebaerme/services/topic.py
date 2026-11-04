"""Topic classification. Filter out not allowed topics."""

from jebaerme.jev.jev import Jev, JevAuthError
from jebaerme.models.jev import BaseJevResponse, NoulAnswer, NoulCriteria, NoulQuestion

__all__ = [
    "TOPIC_NOUL_THRESHOLD",
    "UNAUTHORIZED_TOPIC_MESSAGE",
    "JevAuthError",
    "filter_out_topic",
    "is_topic_allowed",
]

TOPIC_NOUL_THRESHOLD = 0.5
UNAUTHORIZED_TOPIC_MESSAGE = (
    "I can only discuss professional interview topics for a senior software "
    "engineering role. I cannot help with personal details, code generation, "
    "or politics."
)

_TOPIC_NOUL_CRITERIA = NoulCriteria(
    true=(
        "The input is a message that could be addressed during a job interview "
        "in the IT domain to a senior software engineer. The recruiter asks "
        "questions about soft or hard skills to ensure the candidate fits "
        "into their company."
    ),
    false=(
        "The input asks the candidate for sensitive personal details such as "
        "address, phone number, or email. The recruiter asks for code "
        "generation. Politics is a banned topic as well."
    ),
)

_TOPIC_QUESTION = NoulQuestion(
    instructions="Can the message be processed by the system?",
    criteria=_TOPIC_NOUL_CRITERIA,
)


def filter_out_topic(state: str) -> BaseJevResponse:
    jev = Jev({"filter_out": _TOPIC_QUESTION})
    return jev.send(state)


def is_topic_allowed(result: BaseJevResponse) -> bool:
    answer = result.answers.get("filter_out")
    if isinstance(answer, NoulAnswer):
        return answer.noul >= TOPIC_NOUL_THRESHOLD
    return True
