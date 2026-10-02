"""
Test script for OpenRouterLLM.

Run via tox (recommended):
    OPENROUTER_API_KEY=sk-or-... tox -e openrouter

Or with pytest directly:
    OPENROUTER_API_KEY=sk-or-... python -m pytest src/tests/ai_agents/test_openrouter.py -v

Or run directly (manual test):
    OPENROUTER_API_KEY=sk-or-... python src/tests/ai_agents/test_openrouter.py
"""
import asyncio
import os
import sys

import pytest

# Add src to path for imports when running directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from ai_agents.OpenRouterLLM import OpenRouterLLM


# Skip all tests if no API key
pytestmark = pytest.mark.skipif(
    not os.getenv("OPENROUTER_API_KEY"),
    reason="OPENROUTER_API_KEY not set"
)


def print_usage(result: dict, label: str = ""):
    """Helper to print model and token usage from result."""
    meta = result.get("_meta", result)
    model = meta.get("model", "unknown")
    usage = meta.get("usage", {})
    prompt = usage.get("prompt_tokens", 0)
    completion = usage.get("completion_tokens", 0)
    total = usage.get("total_tokens", 0)
    print(f"\n   [{label}] Model: {model}")
    print(f"   [{label}] Tokens: {prompt} prompt + {completion} completion = {total} total")


@pytest.fixture
def llm():
    """Create OpenRouterLLM instance."""
    return OpenRouterLLM()


@pytest.mark.asyncio
async def test_health_check(llm):
    """Test OpenRouter connection."""
    result = await llm.health_check()
    print_usage(result, "health_check")
    assert result.get("healthy") is True, f"Health check failed: {result}"
    assert "model" in result
    assert "usage" in result


@pytest.mark.asyncio
async def test_chat_completion_tracks_usage(llm):
    """_chat_completion returns parsed JSON and accumulates token usage under _meta."""
    result = await llm._chat_completion(
        system_prompt='Respond with ONLY valid JSON, no explanation.',
        user_prompt='Return {"answer": 4} for 2+2. JSON response:',
    )
    print_usage(result, "chat_completion")

    assert "error" not in result, f"Chat completion failed: {result}"
    assert "_meta" in result
    assert result["_meta"]["usage"]["total_tokens"] > 0
    assert result["_meta"]["attempts"] >= 1


# Direct execution for quick manual testing
async def main():
    if not os.getenv("OPENROUTER_API_KEY"):
        print("ERROR: Set OPENROUTER_API_KEY environment variable")
        print("  export OPENROUTER_API_KEY=sk-or-...")
        return

    print("=" * 60)
    print("OpenRouter LLM Test")
    print("=" * 60)

    llm = OpenRouterLLM()
    print(f"\nRequested model: {llm.model}")

    total_tokens = 0

    # Health check
    print("\n" + "-" * 40)
    print("1. Health check")
    print("-" * 40)
    health = await llm.health_check()
    print(f"   Healthy: {health.get('healthy')}")
    print(f"   Model used: {health.get('model')}")
    usage = health.get("usage", {})
    print(f"   Tokens: {usage.get('prompt_tokens', 0)} + {usage.get('completion_tokens', 0)} = {usage.get('total_tokens', 0)}")
    total_tokens += usage.get("total_tokens", 0)

    if not health.get("healthy"):
        print("\nHealth check failed, stopping.")
        return

    # Chat completion
    print("\n" + "-" * 40)
    print("2. Chat completion (JSON + token accounting)")
    print("-" * 40)
    result = await llm._chat_completion(
        system_prompt='Respond with ONLY valid JSON, no explanation.',
        user_prompt='Return {"answer": 4} for 2+2. JSON response:',
    )

    meta = result.get("_meta", {})
    if "error" not in result:
        print(f"   Parsed: {result}")
        print(f"   Model used: {meta.get('model')}")
    else:
        print(f"   ERROR: {result.get('error')}")
    usage = meta.get("usage", {})
    print(f"   Tokens: {usage.get('prompt_tokens', 0)} + {usage.get('completion_tokens', 0)} = {usage.get('total_tokens', 0)}")
    total_tokens += usage.get("total_tokens", 0)

    # Summary
    print("\n" + "=" * 60)
    print(f"TOTAL TOKENS USED: {total_tokens}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
