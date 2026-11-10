"""Create a queued task from a validated coordinator proposal."""

from ..state import CoordinatorState, Task


def create_task(state: CoordinatorState) -> dict:
    proposal = state["coordinator_decision"]["proposal"]

    # Validation has checked the task type and plan position.
    # Task generates its own identity and defaults to queued.
    task = Task(
        task_type=proposal["task_type"],
        title=proposal["title"],
        plan_id=proposal.get("plan_id"),
        sequence_number=proposal.get("sequence_number"),
        inputs=proposal.get("inputs", {}),
    )

    return {
        "tasks": [
            *state["tasks"],
            task.model_dump(mode="json"),
        ]
    }
