"""Assemble the teacher-assistant graph from its runtime dependencies."""

from collections.abc import Callable, Mapping

from langchain_core.runnables import Runnable

from ..llm import LLMCaller, Tier
from .graph import build_teacher_assistant_graph
from .nodes.complete_task import complete_task
from .nodes.coordinator import build_coordinator
from .nodes.create_task import create_task
from .nodes.dispatch_task import dispatch_task
from .nodes.execute_task import build_execute_task
from .nodes.initial_dispatch import build_initial_dispatch
from .nodes.respond import respond
from .nodes.task_validation import build_validation_node
from .raw_homework_processing import build_raw_homework_graph
from .workflow_config import (
    DEFAULT_SETTINGS,
    RAW_HOMEWORK_PROCESSING,
    TASK_REGISTRY,
    TaskDefinition,
    WorkflowSettings,
)


def build_runtime_graph(
    llm_factory: Callable[[Tier], LLMCaller],
    *,
    checkpointer,
    task_registry: Mapping[str, TaskDefinition] | None = None,
    handlers: Mapping[str, Runnable] | None = None,
    settings: WorkflowSettings = DEFAULT_SETTINGS,
    tier: Tier = "cheap",
):
    """Build one compiled graph for the application's shared runtime.

    Task definitions describe coordinator-visible behavior, while handlers
    implement execution. Keeping them separate lets a future handler be a
    subgraph, a tool adapter, or another runnable without changing task state.
    """
    registry = dict(TASK_REGISTRY if task_registry is None else task_registry)
    registered_handlers = (
        {RAW_HOMEWORK_PROCESSING: build_raw_homework_graph()}
        if handlers is None
        else dict(handlers)
    )

    if set(registry) != set(registered_handlers):
        raise ValueError(
            "Task definitions and handlers must register the same task types"
        )

    return build_teacher_assistant_graph(
        initial_dispatch=build_initial_dispatch(registry),
        coordinator=build_coordinator(
            llm_factory,
            task_registry=registry,
            tier=tier,
        ),
        validate_decision=build_validation_node(registry, settings=settings),
        create_task=create_task,
        dispatch_task=dispatch_task,
        execute_task=build_execute_task(registered_handlers),
        complete_task=complete_task,
        respond=respond,
        checkpointer=checkpointer,
    )
