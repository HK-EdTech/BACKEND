"""Create the initial task without asking the coordinator to select it."""

from collections.abc import Mapping

from langchain_core.runnables import RunnableConfig

from ..state import CoordinatorDecision, Task, TeacherAssistantState
from ..workflow_config import TaskDefinition


def build_initial_dispatch(
    task_registry: Mapping[str, TaskDefinition],
):
    registry = dict(task_registry)

    def initial_dispatch(
        state: TeacherAssistantState,
        config: RunnableConfig,
    ) -> dict:
        runtime = config.get("configurable") or {}
        task_type = runtime.get("initial_task_type")

        # Only registered types can select an initial handler.
        if not isinstance(task_type, str) or task_type not in registry:
            raise ValueError("Initial task type is not registered")

        # Starting a task through this entry path requires a fresh conversation;
        # it must not replace tasks or bypass an existing conversation's routing.
        if (
            state["messages"]
            or state["tasks"]
            or state["coordinator_decision"] is not None
        ):
            raise ValueError(
                "Initial dispatch requires empty messages, empty tasks, "
                "and no coordinator decision"
            )

        task = Task(
            task_type=task_type,
            title=task_type.replace("_", " ").capitalize(),
            inputs=runtime.get("initial_task_inputs", {}),
        )

        #this is initial_dispatch decision but it uses CoordinatorDecision for convenience
        decision = CoordinatorDecision(  
            action="dispatch",
            task_id=task.task_id,
        )

        return {
            "tasks": [task.model_dump(mode="json")],
            "coordinator_decision": {
                "proposal": decision.model_dump(mode="json"),
                "validation_error": {
                    "errors": [],
                    "correction_attempts": 0,
                },
            },
        }

    return initial_dispatch
