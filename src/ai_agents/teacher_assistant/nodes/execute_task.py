"""Execute a running task through its registered handler."""

from collections.abc import Mapping

from langchain_core.runnables import (
    Runnable,
    RunnableConfig,
    RunnableLambda,
)

from ..state import Task, TeacherAssistantState
from ..workflow_config import TaskStatus
from .task_validation import validate_handler_result


def build_execute_task(handlers: Mapping[str, Runnable]):
    registered_handlers = dict(handlers)

    async def execute_task(
        state: TeacherAssistantState,
        config: RunnableConfig,
    ) -> dict:
        proposal = state["coordinator_decision"]["proposal"]

        matches = [
            record
            for record in state["tasks"]
            if record["task_id"] == proposal["task_id"]
        ]
        if len(matches) != 1:
            raise ValueError("Expected exactly one selected task")

        task = Task.model_validate(matches[0])
        if task.status != TaskStatus.RUNNING:
            raise ValueError("Task must be running before execution")

        handler = registered_handlers.get(task.task_type)
        if handler is None:
            raise ValueError("No handler is registered for this task type")

        # Give the handler a separate serialized copy of the task.
        output = await handler.ainvoke(
            {"task": task.model_dump(mode="json")},
            config=config,
        )

        def validate_output(value: object) -> Task:
            if not isinstance(value, dict) or "task" not in value:
                raise ValueError("Handler must return a task")

            return validate_handler_result(task, value["task"])

        # Record invalid handler results as a separate failed trace.
        result_validator = RunnableLambda(
            validate_output,
            name="validate_handler_result",
        )
        updated_task = await result_validator.ainvoke(
            output,
            config=config,
        )

        return {
            "tasks": [
                updated_task.model_dump(mode="json")
                if record["task_id"] == task.task_id
                else record
                for record in state["tasks"]
            ]
        }

    return execute_task
