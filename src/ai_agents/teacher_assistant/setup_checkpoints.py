"""Explicitly initialize or migrate the LangGraph checkpoint database.

Run from the repository root before starting the application:
    python -m src.ai_agents.teacher_assistant.setup_checkpoints

Uses LANGGRAPH_DATABASE_URL from the environment or .env. Deployment must run
this command once, using the same application image that will serve requests.
"""

import asyncio
import os

from dotenv import load_dotenv
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


async def main() -> None:
    load_dotenv()
    checkpoint_url = os.getenv("LANGGRAPH_DATABASE_URL")
    if not checkpoint_url:
        raise RuntimeError("Set LANGGRAPH_DATABASE_URL for checkpoint setup")

    print("Applying pending LangGraph checkpoint migrations...", flush=True)
    async with AsyncPostgresSaver.from_conn_string(checkpoint_url) as checkpointer:
        await checkpointer.setup()
    print("LangGraph checkpoint database is ready.", flush=True)


if __name__ == "__main__":
    # Failures propagate and exit nonzero so deployment stops before startup.
    asyncio.run(main())
