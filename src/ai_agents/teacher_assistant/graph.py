"""Parent graph topology for the general teacher assistant."""

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from .state import TeacherAssistantState


def route_entry(
    state: TeacherAssistantState,
    config: RunnableConfig,
) -> str:
    # The adapter supplies this only when starting a new conversation with an
    # initial submission. Later invocations must omit the entry directive.
    runtime = config.get("configurable") or {}
    if runtime.get("initial_task_type") is not None:
        return "initial_dispatch"
    return "coordinator"


def route_action(state: TeacherAssistantState) -> str:
    envelope = state["coordinator_decision"]

    # Rejected proposals return to the coordinator for correction. Validation
    # supplies a fallback respond proposal when its correction budget runs out.
    if envelope["validation_error"]["errors"]:
        return "coordinator"

    return envelope["proposal"]["action"]


def build_teacher_assistant_graph(
    *,
    initial_dispatch,
    coordinator,
    validate_decision,
    create_task,
    dispatch_task,
    execute_task,
    complete_task,
    respond,
    checkpointer,
):
    """Connect supplied node implementations into the parent workflow.

    Node implementations live in nodes/. Supplying them here keeps model
    clients, task handlers, and other runtime dependencies outside graph state.
    """
    builder = StateGraph(TeacherAssistantState)

    builder.add_node("initial_dispatch", initial_dispatch)
    builder.add_node("coordinator", coordinator)
    builder.add_node("validate_decision", validate_decision)
    builder.add_node("create_task", create_task)
    builder.add_node("dispatch_task", dispatch_task)
    builder.add_node("execute_task", execute_task)
    builder.add_node("complete_task", complete_task)
    builder.add_node("respond", respond)

    builder.add_conditional_edges(
        START,
        route_entry,
        {
            "initial_dispatch": "initial_dispatch",
            "coordinator": "coordinator",
        },
    )

    # Initial dispatch constructs its task and decision deterministically, so
    # it bypasses model-decision validation and enters execution directly.
    builder.add_edge("initial_dispatch", "dispatch_task")
    builder.add_edge("coordinator", "validate_decision")

    builder.add_conditional_edges(
        "validate_decision",
        route_action,
        {
            "coordinator": "coordinator",
            "respond": "respond",
            "create_task": "create_task",
            "dispatch": "dispatch_task",
            "complete_task": "complete_task",
        },
    )

    # Save the running task before invoking its handler, then return its
    # validated result to the coordinator rather than draining queued tasks.
    builder.add_edge("dispatch_task", "execute_task")
    builder.add_edge("execute_task", "coordinator")

    # Other task actions also return control to the coordinator.
    builder.add_edge("create_task", "coordinator")
    builder.add_edge("complete_task", "coordinator")

    # End this turn while preserving the checkpointed conversation.
    builder.add_edge("respond", END)

    return builder.compile(checkpointer=checkpointer)
