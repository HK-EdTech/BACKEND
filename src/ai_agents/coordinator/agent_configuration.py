"""Agent configurations and shared coordinator workflow settings."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from .task_definitions import (
    RAW_HOMEWORK_PROCESSING,
    RAW_HOMEWORK_PROCESSING_TASK,
    TaskDefinition,
)

if TYPE_CHECKING:
    from langchain_core.runnables import Runnable


class TaskStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    RESULT_READY = "result_ready"
    COMPLETED = "completed"


@dataclass(frozen=True)
class WorkflowSettings:
    """Decision-correction settings shared by coordinator workflows."""

    # Additional attempts after a decision fails validation.
    # Zero disables correction; a new decision gets a fresh budget.
    max_decision_corrections: int = 2

    def __post_init__(self) -> None:
        if self.max_decision_corrections < 0:
            raise ValueError("max_decision_corrections must not be negative")


@dataclass(frozen=True)
class AgentConfiguration:
    """Capabilities and purpose supplied to a coordinator graph."""

    task_registry: Mapping[str, TaskDefinition]
    # Build handlers during runtime assembly, rather than at module import.
    handler_builders: Mapping[str, Callable[[], Runnable]]
    coordinator_instructions: str


def _build_raw_homework_handler():
    # Defer the import: the subgraph's task state uses TaskStatus above.
    from .raw_homework_processing import build_raw_homework_graph

    return build_raw_homework_graph()


HOMEWORK_MARKING_TASK_REGISTRY: dict[str, TaskDefinition] = {
    RAW_HOMEWORK_PROCESSING: RAW_HOMEWORK_PROCESSING_TASK,
}

HOMEWORK_MARKING = AgentConfiguration(
    task_registry=HOMEWORK_MARKING_TASK_REGISTRY,
    handler_builders={RAW_HOMEWORK_PROCESSING: _build_raw_homework_handler},
    coordinator_instructions=(
        "You coordinate a homework marking assistant for teachers. "
        "Help the teacher prepare homework materials and manage the registered "
        "homework tasks. Explain task results and issues to the teacher, request "
        "guidance when needed, and obtain teacher approval for tasks that require it. "
        "Only offer task execution for registered task types, and only claim "
        "work has completed when the task state confirms it."
    ),
)

DEFAULT_SETTINGS = WorkflowSettings()
