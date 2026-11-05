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

TOPIC_NOUL_THRESHOLD = 0.75
UNAUTHORIZED_TOPIC_MESSAGE = (
    "I can only discuss professional interview topics for a senior software "
    "engineering role. I cannot help with personal details, code generation, "
    "or politics."
)

_TOPIC_NOUL_CRITERIA = NoulCriteria(
    true=(
        "The state is a message that could be addressed during a job interview "
        "in the IT domain to a senior software engineer or an AI engineer. "
        "The recruiter asks "
        "questions about soft or hard skills to ensure the candidate fits "
        "into their company. A recruiter could also asks high-level thinking "
        "on technical problems. While question about organisational matters, "
        "even if personal, are allowed."
    ),
    false=(
        "The input asks the candidate for sensitive personal details such as "
        "address, phone number, or email. The input is not relevant to the "
        "ability to perform the job. The recruiter asks for code generation"
        "or deep thinking on complex architecture that does not land in a "
        "tchip chat interview. Direct or indirect probes into protected "
        "characteristics, family status, health, origin, political views, "
        "or salary history."
    ),
)

_TOPIC_QUESTION = NoulQuestion(
    instructions=(
        "A HR or technical recruiter sends a message to evaluate a "
        "candidate during a job interview. But all messages should not "
        "trigger the system. Is this message safe to be processes?"
    ),
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
