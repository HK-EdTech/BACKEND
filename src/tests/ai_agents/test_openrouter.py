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
import json
import os
import sys

import pytest
import pytest_asyncio

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


@pytest.fixture
def llm_with_reasoning():
    """Create OpenRouterLLM instance with reasoning enabled."""
    return OpenRouterLLM(enable_reasoning=True)


@pytest.mark.asyncio
async def test_health_check(llm):
    """Test OpenRouter connection."""
    result = await llm.health_check()
    print_usage(result, "health_check")
    assert result.get("healthy") is True, f"Health check failed: {result}"
    assert "model" in result
    assert "usage" in result


@pytest.mark.asyncio
async def test_process_ocr_result(llm):
    """Test OCR text processing and extraction."""
    sample_ocr = """
    Student Name: J0hn Sm1th
    Date: 2024-O1-15
    Score: 85/1OO
    """

    result = await llm.process_ocr_result(
        sample_ocr,
        expected_fields=["student_name", "date", "score"]
    )
    print_usage(result, "process_ocr")

    assert "error" not in result, f"OCR processing failed: {result}"
    assert "extracted_data" in result
    assert "confidence" in result
    assert "_meta" in result
    assert "usage" in result["_meta"]


@pytest.mark.asyncio
async def test_validate_homework_answer_correct(llm):
    """Test homework validation with correct answer."""
    result = await llm.validate_homework_answer(
        student_answer="4",
        expected_answer="4",
        question="What is 2+2?"
    )
    print_usage(result, "validate_correct")

    assert "error" not in result, f"Validation failed: {result}"
    assert result.get("is_correct") is True
    assert result.get("score", 0) >= 0.9


@pytest.mark.asyncio
async def test_validate_homework_answer_incorrect(llm):
    """Test homework validation with incorrect answer."""
    result = await llm.validate_homework_answer(
        student_answer="5",
        expected_answer="4",
        question="What is 2+2?"
    )
    print_usage(result, "validate_incorrect")

    assert "error" not in result, f"Validation failed: {result}"
    assert result.get("is_correct") is False
    assert result.get("score", 1) < 0.5


@pytest.mark.asyncio
async def test_validate_with_reasoning(llm_with_reasoning):
    """Test validation with reasoning enabled."""
    result = await llm_with_reasoning.validate_homework_answer(
        student_answer="3.14159",
        expected_answer="pi",
        question="What is the ratio of a circle's circumference to its diameter?"
    )
    print_usage(result, "validate_reasoning")

    assert "error" not in result, f"Validation failed: {result}"
    assert "_meta" in result
    assert result["_meta"]["reasoning_enabled"] is True


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

    # Process OCR
    print("\n" + "-" * 40)
    print("2. Processing sample OCR text")
    print("-" * 40)
    sample_ocr = """
    Student Name: J0hn Sm1th
    Date: 2024-O1-15
    Score: 85/1OO
    """
    result = await llm.process_ocr_result(
        sample_ocr,
        expected_fields=["student_name", "date", "score"]
    )

    if "error" not in result:
        print(f"   Extracted: {json.dumps(result.get('extracted_data', {}), indent=2)}")
        print(f"   Confidence: {result.get('confidence')}")
        meta = result.get("_meta", {})
        print(f"   Model used: {meta.get('model')}")
        usage = meta.get("usage", {})
        print(f"   Tokens: {usage.get('prompt_tokens', 0)} + {usage.get('completion_tokens', 0)} = {usage.get('total_tokens', 0)}")
        total_tokens += usage.get("total_tokens", 0)
    else:
        print(f"   ERROR: {result.get('error')}")

    # Validate answer
    print("\n" + "-" * 40)
    print("3. Validating homework answer (correct)")
    print("-" * 40)
    validation = await llm.validate_homework_answer(
        student_answer="4",
        expected_answer="4",
        question="What is 2+2?"
    )

    if "error" not in validation:
        print(f"   Is correct: {validation.get('is_correct')}")
        print(f"   Score: {validation.get('score')}")
        print(f"   Feedback: {validation.get('feedback')}")
        meta = validation.get("_meta", {})
        print(f"   Model used: {meta.get('model')}")
        usage = meta.get("usage", {})
        print(f"   Tokens: {usage.get('prompt_tokens', 0)} + {usage.get('completion_tokens', 0)} = {usage.get('total_tokens', 0)}")
        total_tokens += usage.get("total_tokens", 0)
    else:
        print(f"   ERROR: {validation.get('error')}")

    # Summary
    print("\n" + "=" * 60)
    print(f"TOTAL TOKENS USED: {total_tokens}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
