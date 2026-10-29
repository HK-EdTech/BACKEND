"""Task definitions and settings for the teacher assistant workflow."""

from dataclasses import dataclass
from enum import StrEnum


class TaskStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    RESULT_READY = "result_ready"
    COMPLETED = "completed"


@dataclass(frozen=True)
class TaskDefinition:
    """Describe a supported task type independently of its handler."""

    description: str
    approval_required: bool = False


@dataclass(frozen=True)
class WorkflowSettings:
    """Decision-correction settings for the teacher assistant."""

    # Additional attempts after a decision fails validation.
    # Zero disables correction; a new decision gets a fresh budget.
    max_decision_corrections: int = 2

    def __post_init__(self) -> None:
        if self.max_decision_corrections < 0:
            raise ValueError(
                "max_decision_corrections must not be negative"
            )


RAW_HOMEWORK_PROCESSING = "raw_homework_processing"

TASK_REGISTRY: dict[str, TaskDefinition] = {
    RAW_HOMEWORK_PROCESSING: TaskDefinition(
        description=(
            "Process teacher-supplied homework material and prepare "
            "a result for teacher approval."
        ),
        approval_required=True,
    ),
}

DEFAULT_SETTINGS = WorkflowSettings()
