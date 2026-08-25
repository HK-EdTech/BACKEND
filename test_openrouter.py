"""
Quick test script for OpenRouterLLM.
Run: OPENROUTER_API_KEY=your_key python test_openrouter.py
"""
import asyncio
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from ai_agents.OpenRouterLLM import OpenRouterLLM


async def main():
    # Check for API key
    if not os.getenv("OPENROUTER_API_KEY"):
        print("ERROR: Set OPENROUTER_API_KEY environment variable")
        print("  export OPENROUTER_API_KEY=sk-or-...")
        return

    print("=== OpenRouter LLM Test ===\n")

    llm = OpenRouterLLM()
    print(f"Using model: {llm.model}\n")

    # Test 1: Health check
    print("1. Health check...")
    health = await llm.health_check()
    print(f"   Result: {health}\n")

    if not health.get("healthy"):
        print("Health check failed, stopping tests.")
        return

    # Test 2: Process sample OCR text
    print("2. Processing sample OCR text...")
    sample_ocr = """
    Student Name: J0hn Sm1th
    Date: 2024-O1-15
    Score: 85/1OO

    Question 1: What is 2+2?
    Answer: 4

    Question 2: SpelI 'cat'
    Answer: cat
    """

    result = await llm.process_ocr_result(
        sample_ocr, expected_fields=["student_name", "date", "score", "answers"]
    )
    print(f"   Extracted data: {result}\n")

    # Test 3: Validate homework answer
    print("3. Validating homework answer...")
    validation = await llm.validate_homework_answer(
        student_answer="4",
        expected_answer="4",
        question="What is 2+2?",
    )
    print(f"   Validation: {validation}\n")

    print("=== All tests complete ===")


if __name__ == "__main__":
    asyncio.run(main())
