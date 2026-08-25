import os
import json
from pathlib import Path
from typing import Any
import httpx

from ..utils.logger import get_logger

logger = get_logger(name=__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
CONFIG_PATH = Path(__file__).parent.parent.parent / "cfg" / "free_models.cfg"


def load_free_models(config_path: Path = CONFIG_PATH) -> list[str]:
    """Load free models from config file."""
    models = []
    if config_path.exists():
        with open(config_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    models.append(line)
    if not models:
        # Fallback if config is missing or empty
        models = ["meta-llama/llama-3.2-3b-instruct:free"]
        logger.warning(f"No models in {config_path}, using fallback: {models[0]}")
    return models


class OpenRouterLLM:
    """
    OpenRouter LLM client for processing OCR results.
    Uses free models available on OpenRouter to structure and validate OCR output.

    Note: Free models on OpenRouter do NOT support tool/function calling (skills).
    They are text-in/text-out only. For tool use, you need paid models like
    Claude, GPT-4, or Gemini Pro.
    """

    FREE_MODELS = load_free_models()

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """
        Initialize the OpenRouter client.

        Args:
            api_key: OpenRouter API key. Falls back to OPENROUTER_API_KEY env var.
            model: Model to use. Defaults to first free model.
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key required. Set OPENROUTER_API_KEY env var or pass api_key."
            )
        self.model = model or self.FREE_MODELS[0]
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": os.getenv("APP_URL", "http://localhost:8000"),
            "X-Title": "HK EdTech OCR Processing",
        }

    async def process_ocr_result(
        self, ocr_text: str, expected_fields: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Process OCR text and extract structured data.

        Args:
            ocr_text: Raw text from OCR
            expected_fields: Optional list of fields to extract (e.g., ["name", "date", "score"])

        Returns:
            Dict with extracted fields and confidence
        """
        field_instruction = ""
        if expected_fields:
            field_instruction = f"\nExtract these specific fields: {', '.join(expected_fields)}"

        system_prompt = """You are an OCR post-processor. Your job is to:
1. Clean up and structure raw OCR text
2. Extract key information into structured fields
3. Fix obvious OCR errors (like 0/O, 1/l confusion)
4. Rate your confidence in the extraction (0.0 to 1.0)

Always respond with valid JSON in this format:
{
  "extracted_data": { ... },
  "cleaned_text": "...",
  "confidence": 0.0-1.0,
  "corrections_made": ["list of OCR errors you fixed"]
}"""

        user_prompt = f"""Process this OCR text and extract structured data:{field_instruction}

OCR TEXT:
{ocr_text}

Respond with JSON only."""

        return await self._chat_completion(system_prompt, user_prompt)

    async def validate_homework_answer(
        self, student_answer: str, expected_answer: str, question: str | None = None
    ) -> dict[str, Any]:
        """
        Validate a student's answer against expected answer.

        Args:
            student_answer: The OCR-extracted student answer
            expected_answer: The correct answer
            question: Optional question text for context

        Returns:
            Dict with is_correct, score, feedback
        """
        context = f"Question: {question}\n" if question else ""

        system_prompt = """You are a homework grading assistant. Compare the student's answer to the expected answer.
Consider:
- Partial credit for partially correct answers
- Common OCR errors that might affect the text
- Mathematical equivalence (e.g., 1/2 = 0.5)

Respond with JSON:
{
  "is_correct": true/false,
  "score": 0.0-1.0,
  "feedback": "brief explanation",
  "ocr_issues_detected": ["any suspected OCR errors"]
}"""

        user_prompt = f"""{context}Student's answer: {student_answer}
Expected answer: {expected_answer}

Grade this answer and respond with JSON only."""

        return await self._chat_completion(system_prompt, user_prompt)

    async def _chat_completion(
        self, system_prompt: str, user_prompt: str
    ) -> dict[str, Any]:
        """
        Make a chat completion request to OpenRouter.

        Returns:
            Parsed JSON response or error dict
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,  # Low temperature for consistent extraction
            "max_tokens": 1000,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    OPENROUTER_API_URL,
                    headers=self.headers,
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()

                content = result["choices"][0]["message"]["content"]
                logger.info(f"OpenRouter response received, model: {self.model}")

                # Parse JSON from response (handle markdown code blocks)
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]

                return json.loads(content.strip())

        except httpx.HTTPStatusError as e:
            logger.error(f"OpenRouter API error: {e.response.status_code} - {e.response.text}")
            return {"error": f"API error: {e.response.status_code}", "details": e.response.text}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return {"error": "Invalid JSON response", "raw_content": content}
        except Exception as e:
            logger.error(f"OpenRouter request failed: {e}")
            return {"error": str(e)}

    async def health_check(self) -> dict[str, Any]:
        """Test the OpenRouter connection with a simple request."""
        try:
            result = await self._chat_completion(
                "You are a test assistant.",
                "Respond with exactly: {\"status\": \"ok\"}",
            )
            return {"healthy": result.get("status") == "ok", "model": self.model, "response": result}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
