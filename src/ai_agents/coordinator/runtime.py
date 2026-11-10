"""Assemble a coordinator graph using an agent configuration."""

from collections.abc import Callable

from ..llm import LLMCaller, Tier
from .graph import build_coordinator_graph
from .nodes.complete_task import complete_task
from .nodes.coordinator import build_coordinator
from .nodes.create_task import create_task
from .nodes.dispatch_task import dispatch_task
from .nodes.execute_task import build_execute_task
from .nodes.initial_dispatch import build_initial_dispatch
from .nodes.respond import respond
from .nodes.task_validation import build_validation_node
from .agent_configuration import (
    AgentConfiguration,
    DEFAULT_SETTINGS,
    WorkflowSettings,
)


def build_runtime_graph(
    llm_factory: Callable[[Tier], LLMCaller],
    *,
    checkpointer,
    configuration: AgentConfiguration,
    settings: WorkflowSettings = DEFAULT_SETTINGS,
    tier: Tier = "cheap",
):
    """Build one compiled graph for the application's shared runtime.

    Task definitions describe coordinator-visible behavior, while handlers
    implement execution. Keeping them separate lets a future handler be a
    subgraph, a tool adapter, or another runnable without changing task state.
    """
    registry = dict(configuration.task_registry)

    if set(registry) != set(configuration.handler_builders):
        raise ValueError(
            "Task definitions and handlers must register the same task types"
        )

    registered_handlers = {
        task_type: build_handler()
        for task_type, build_handler in configuration.handler_builders.items()
    }

    return build_coordinator_graph(
        initial_dispatch=build_initial_dispatch(registry),
        coordinator=build_coordinator(
            llm_factory,
            task_registry=registry,
            coordinator_instructions=configuration.coordinator_instructions,
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
