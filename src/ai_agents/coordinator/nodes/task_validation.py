"""Central decision validation and separate handler-result validation."""

from collections.abc import Mapping

from langchain_core.runnables import RunnableConfig, RunnableLambda
from pydantic import ValidationError

from ..state import (
    CoordinatorDecision,
    Task,
    CoordinatorState,
    validate_coordinator_decision,
    validate_task_list,
)
from ..agent_configuration import (
    DEFAULT_SETTINGS,
    TaskStatus,
    WorkflowSettings,
)
from ..task_definitions import TaskDefinition


def build_decision_validator(
    task_registry: Mapping[str, TaskDefinition],
) -> RunnableLambda:
    """Build one traced operation for all pre-action decision checks."""
    registry = dict(task_registry)

    def validate(
        state: CoordinatorState,
        config: RunnableConfig,
    ) -> CoordinatorDecision:
        # Call the plain helper, not its runnable wrapper, so format and task
        # checks belong to one validation trace rather than two nested traces.
        envelope = state["coordinator_decision"]
        if envelope is None:
            raise ValueError("No coordinator decision was proposed")
        decision = validate_coordinator_decision(envelope["proposal"])
        if decision.action == "respond":
            return decision

        tasks = validate_task_list(state["tasks"])
        identities = [task.task_id for task in tasks]
        # Updates target an ID, so duplicate IDs would make selection ambiguous.
        if len(identities) != len(set(identities)):
            raise ValueError("Task IDs must be unique within the conversation")

        if decision.action == "create_task":
            if decision.task_type not in registry:
                raise ValueError("Task type is not registered")
            candidate = Task(
                task_type=decision.task_type,
                title=decision.title,
                plan_id=decision.plan_id,
                sequence_number=decision.sequence_number,
                inputs=decision.inputs,
            )
            # Check prospective plan positions before the creation node mutates
            # state. This candidate is validated only; it is not stored here.
            validate_task_list([
                *state["tasks"], candidate.model_dump(mode="json"),
            ])
            return decision

        matches = [task for task in tasks if task.task_id == decision.task_id]
        if len(matches) != 1:
            raise ValueError("The selected task does not exist")
        task = matches[0]
        if task.task_type not in registry:
            raise ValueError("Task type is not registered")

        # These permissions come from the application's interpretation of an
        # explicit user action, never from model-generated decision fields.
        runtime = config.get("configurable") or {}
        approved_ids = runtime.get("user_approved_task_ids", ())
        retry_ids = runtime.get("user_retry_task_ids", ())

        if decision.action == "dispatch":
            if task.status not in (TaskStatus.QUEUED, TaskStatus.RESULT_READY):
                raise ValueError("Only queued or result_ready tasks can run")
            if (
                task.status == TaskStatus.RESULT_READY
                and not decision.guidance
                and task.task_id not in retry_ids
            ):
                raise ValueError(
                    "Rerunning a task requires guidance or an explicit retry"
                )

            # Plan order is local to a plan. Other plans and standalone tasks
            # do not block dispatch merely because they are also queued.
            if task.plan_id is not None:
                earlier_tasks = [
                    other for other in tasks
                    if other.plan_id == task.plan_id
                    and other.sequence_number < task.sequence_number
                ]
                if any(
                    other.status != TaskStatus.COMPLETED
                    for other in earlier_tasks
                ):
                    raise ValueError(
                        "Earlier tasks in this plan must be completed first"
                    )

        elif decision.action == "complete_task":
            if task.status != TaskStatus.RESULT_READY:
                raise ValueError("Only result_ready tasks can be completed")
            # User approval cannot bypass issues or execution errors.
            if task.has_issues or task.error:
                raise ValueError("Resolve task issues and errors before completion")
            if (
                registry[task.task_type].approval_required
                and task.task_id not in approved_ids
            ):
                raise ValueError("This task requires explicit user approval")

        return decision

    # The graph catches errors outside this runnable so LangSmith can record
    # validation failure while the outer node requests correction or recovers.
    return RunnableLambda(validate, name="validate_coordinator_action")


def build_validation_node(
    task_registry: Mapping[str, TaskDefinition],
    *,
    settings: WorkflowSettings = DEFAULT_SETTINGS,
):
    validator = build_decision_validator(task_registry)

    async def validate_decision(
        state: CoordinatorState,
        config: RunnableConfig,
    ) -> dict:
        envelope = state["coordinator_decision"] or {
            "proposal": {},
            "validation_error": {
                "errors": [],
                "correction_attempts": 0,
            },
        }
        attempts = envelope["validation_error"]["correction_attempts"]

        try:
            decision = await validator.ainvoke(state, config=config)
        except ValueError as exc:
            # The inner runnable records the failure before we catch it.
            if isinstance(exc, ValidationError):
                errors = [
                    f"{error['loc']}: {error['msg']}"
                    for error in exc.errors(
                        include_input=False,
                        include_url=False,
                    )
                ]
            else:
                errors = [str(exc)]

            if attempts < settings.max_decision_corrections:
                # Preserve the rejected proposal and task list. Conditional
                # routing will return validation errors to the coordinator.
                return {
                    "coordinator_decision": {
                        "proposal": envelope["proposal"],
                        "validation_error": {
                            "errors": errors,
                            "correction_attempts": attempts + 1,
                        },
                    }
                }

            # Exhausting this decision's correction budget ends correction.
            # Clear errors so conditional routing selects the fallback action.
            decision = CoordinatorDecision(
                action="respond",
                response=(
                    "I couldn't determine a valid next action. "
                    "Please try again."
                ),
            )

        return {
            "coordinator_decision": {
                "proposal": decision.model_dump(mode="json"),
                "validation_error": {
                    "errors": [],
                    "correction_attempts": attempts,
                },
            }
        }

    return validate_decision


def validate_handler_result(dispatched_task: Task, value: object) -> Task:
    """Validate a handler's returned task after execution, not before it."""
    returned_task = Task.model_validate(value)
    if returned_task.status != TaskStatus.RESULT_READY:
        raise ValueError("Handlers must return result_ready")

    # Handlers can change results, issues, and errors, but not the identity,
    # original inputs, plan membership, or guidance managed by the parent.
    for name in (
        "task_id", "task_type", "title", "plan_id", "sequence_number",
        "inputs", "guidance",
    ):
        if getattr(returned_task, name) != getattr(dispatched_task, name):
            raise ValueError(f"Handler changed protected field: {name}")
    return returned_task
