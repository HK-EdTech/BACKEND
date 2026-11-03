"""Complete a task after its coordinator decision passes validation."""

from ..state import Task, TeacherAssistantState
from ..workflow_config import TaskStatus


def complete_task(state: TeacherAssistantState) -> dict:
    proposal = state["coordinator_decision"]["proposal"]

    matches = [
        record
        for record in state["tasks"]
        if record["task_id"] == proposal["task_id"]
    ]
    if len(matches) != 1:
        raise ValueError("Expected exactly one selected task")

    # Central validation has checked result_ready status, outstanding
    # issues, and any required teacher approval.
    task = Task.model_validate(matches[0])
    task.status = TaskStatus.COMPLETED

    return {
        "tasks": [
            task.model_dump(mode="json")
            if record["task_id"] == task.task_id
            else record
            for record in state["tasks"]
        ]
    }
