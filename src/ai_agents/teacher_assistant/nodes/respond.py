"""Add the coordinator's response to the shared conversation."""

from langchain_core.messages import AIMessage

from ..state import TeacherAssistantState


def respond(state: TeacherAssistantState) -> dict:
    proposal = state["coordinator_decision"]["proposal"]

    # Validation has ensured that respond contains nonblank text.
    # The messages reducer appends this message to existing history.
    return {
        "messages": [
            AIMessage(content=proposal["response"]),
        ]
    }
