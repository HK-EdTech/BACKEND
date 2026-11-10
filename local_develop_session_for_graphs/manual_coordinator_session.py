"""Run a local conversation using a selected coordinator agent configuration.

Prepare the checkpoint database explicitly before first use or after a
checkpoint package upgrade (from the repository root):
    python -m src.ai_agents.coordinator.setup_checkpoints

Then start a session:
    python -m local_develop_session_for_graphs.manual_coordinator_session --agent-configuration HOMEWORK_MARKING

To reopen a saved conversation, use the same agent configuration and its thread ID:
    python -m local_develop_session_for_graphs.manual_coordinator_session --agent-configuration HOMEWORK_MARKING --thread-id YOUR_CONVERSATION_ID

This deliberately omits initial_task_type, so the parent graph routes straight
to the coordinator. The coordinator can still dispatch registered task handlers
when requested. Select the agent using --agent-configuration.
"""

import asyncio
import argparse
import os
from uuid import uuid4

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.ai_agents.llm import make_llm_factory
from src.ai_agents.coordinator.runtime import build_runtime_graph
from src.ai_agents.coordinator.agent_configuration import AgentConfiguration, HOMEWORK_MARKING


# Add named configurations here to make them available on the command line.
AGENT_CONFIGURATIONS = {"HOMEWORK_MARKING": HOMEWORK_MARKING}


async def main(agent_configuration: AgentConfiguration, thread_id: str | None = None) -> None:
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("Set OPENROUTER_API_KEY before running this session")

    checkpoint_url = os.getenv("LANGGRAPH_DATABASE_URL")
    if not checkpoint_url:
        raise RuntimeError("Set LANGGRAPH_DATABASE_URL before running this session")

    conversation_id = thread_id or f"manual-coordinator-{uuid4()}"
    config = {
        "configurable": {"thread_id": conversation_id},
        "run_name": "manual_coordinator_session",
        "tags": ["local", "manual-session"],
        "metadata": {"conversation_id": conversation_id},
    }
    async with AsyncPostgresSaver.from_conn_string(checkpoint_url) as checkpointer:
        # Connect to tables prepared by the explicit setup command. Starting
        # a conversation must not create tables or apply migrations.
        graph = build_runtime_graph(
            make_llm_factory(api_key),
            checkpointer=checkpointer,
            configuration=agent_configuration,
        )
        snapshot = await graph.aget_state(config)
        if snapshot.next:
            raise RuntimeError(
                "This thread has unfinished execution. Use a new thread ID; "
                "resuming interrupted execution is not supported by this session."
            )
        first_turn = not snapshot.values

        print(f"Conversation: {conversation_id}")
        print("Reuse it after restarting with --thread-id <conversation-id>.")
        print("Enter a message. Type /quit to exit.")

        while True:
            user_message = input("User> ").strip()
            if user_message == "/quit":
                return
            if not user_message:
                continue

            state = {"messages": [HumanMessage(content=user_message)]}
            if first_turn:
                # Initialize only a new thread; preserve existing saved tasks
                # and decisions when reopening a conversation.
                state.update({"tasks": [], "coordinator_decision": None})

            result = await graph.ainvoke(state, config=config)
            first_turn = False
            messages = result["messages"]
            print(f"Assistant> {messages[-1].content}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--agent-configuration",
        required=True,
        choices=AGENT_CONFIGURATIONS,
        help="Agent configuration used to build the coordinator graph",
    )
    parser.add_argument("--thread-id", help="Reopen a saved conversation")
    args = parser.parse_args()
    asyncio.run(main(AGENT_CONFIGURATIONS[args.agent_configuration], args.thread_id))
