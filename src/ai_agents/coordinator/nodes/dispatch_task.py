"""Prepare a selected task for execution."""

from ..state import CoordinatorState, Task
from ..agent_configuration import TaskStatus


def dispatch_task(state: CoordinatorState) -> dict:
    envelope = state["coordinator_decision"]
    proposal = envelope["proposal"]

    # The proposal has already been validated, or was constructed by
    # initial dispatch. Resolve its task without repeating decision checks.
    matches = [
        record
        for record in state["tasks"]
        if record["task_id"] == proposal["task_id"]
    ]
    if len(matches) != 1:
        raise ValueError("Expected exactly one selected task")
    task = Task.model_validate(matches[0])

    guidance = proposal.get("guidance")
    if guidance:
        task.guidance.append(guidance)

    task.status = TaskStatus.RUNNING

    # Returning the running task lets the graph save this transition before
    # the separate execution node invokes the registered handler.
    return {
        "tasks": [
            task.model_dump(mode="json")
            if record["task_id"] == task.task_id
            else record
            for record in state["tasks"]
        ]
    }
