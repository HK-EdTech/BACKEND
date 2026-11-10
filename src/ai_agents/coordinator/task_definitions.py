"""Individual task definitions that agent configurations can reuse."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskDefinition:
    """Describe a supported task type independently of its handler."""

    description: str
    approval_required: bool = False


RAW_HOMEWORK_PROCESSING = "raw_homework_processing"

RAW_HOMEWORK_PROCESSING_TASK = TaskDefinition(
    description=(
        "Process teacher-supplied homework material and prepare "
        "a result for teacher approval."
    ),
    approval_required=True,
)
