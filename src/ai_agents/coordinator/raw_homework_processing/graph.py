"""Placeholder subgraph for raw homework processing."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from ..state import Task
from ..agent_configuration import TaskStatus
from ..task_definitions import RAW_HOMEWORK_PROCESSING


class RawHomeworkState(TypedDict):
    task: dict


def placeholder(state: RawHomeworkState) -> RawHomeworkState:
    task = Task.model_validate(state["task"])

    # Reject routing mistakes rather than processing another task type.
    if task.task_type != RAW_HOMEWORK_PROCESSING:
        raise ValueError("Expected a raw_homework_processing task")

    task.status = TaskStatus.RESULT_READY
    task.result = None
    task.error = "not_implemented"

    # Temporary issue contents until the issue contract is designed.
    task.moderate_issues = [{
        "code": "not_implemented",
        "message": "Raw homework processing has not been implemented yet.",
    }]

    return {"task": task.model_dump(mode="json")}


def build_raw_homework_graph():
    builder = StateGraph(RawHomeworkState)
    builder.add_node("placeholder", placeholder)
    builder.add_edge(START, "placeholder")
    builder.add_edge("placeholder", END)
    return builder.compile()
