import os
import json
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI

try:
    # When running as part of src package (FastAPI)
    from ..utils.logger import get_logger
except ImportError:
    # When running standalone (tox/pytest with PYTHONPATH=src)
    from utils.logger import get_logger

logger = get_logger(name=__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
CONFIG_PATH = Path(__file__).parent.parent.parent / "cfg" / "free_models.cfg"

# Use OpenRouter's free router - it auto-selects available free models
DEFAULT_MODEL = "openrouter/free"


def load_free_models(config_path: Path = CONFIG_PATH) -> list[str]:
    """Load free models from config file."""
    models = []
    if config_path.exists():
        with open(config_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    models.append(line)
    return models if models else [DEFAULT_MODEL]


class OpenRouterLLM:
    """
    OpenRouter LLM client for processing OCR results.
    Uses OpenAI SDK with OpenRouter's base_url for compatibility.

    Note: We use specific models from cfg/free_models.cfg rather than
    'openrouter/free' because the auto-router can pick content-safety
    or specialized models that don't follow JSON instructions.
    """

    # Reference list from cfg/free_models.cfg
    FREE_MODELS = load_free_models()

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        enable_reasoning: bool = False,
    ):
        """
        Initialize the OpenRouter client using OpenAI SDK.

        Args:
            api_key: OpenRouter API key. Falls back to OPENROUTER_API_KEY env var.
            model: Model to use. Defaults to first model in cfg/free_models.cfg.
            enable_reasoning: Enable reasoning mode for step-by-step thinking.
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key required. Set OPENROUTER_API_KEY env var or pass api_key."
            )

        # Use specified model, or first from config, or fallback
        self.model = model or (self.FREE_MODELS[0] if self.FREE_MODELS else DEFAULT_MODEL)
        self.enable_reasoning = enable_reasoning

        # Use OpenAI SDK with OpenRouter base URL
        self.client = AsyncOpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=self.api_key,
            default_headers={
                "HTTP-Referer": os.getenv("APP_URL", "http://localhost:8000"),
                "X-Title": "HK EdTech Post OCR Processing",
            },
        )

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

IMPORTANT: Respond with ONLY valid JSON, no explanation. Use this format:
{"extracted_data": {...}, "cleaned_text": "...", "confidence": 0.95, "corrections_made": ["..."]}"""

        user_prompt = f"""Process this OCR text and extract structured data:{field_instruction}

OCR TEXT:
{ocr_text}

JSON response:"""

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

IMPORTANT: Respond with ONLY valid JSON, no explanation. Use this format:
{"is_correct": true, "score": 1.0, "feedback": "...", "ocr_issues_detected": []}"""

        user_prompt = f"""{context}Student's answer: {student_answer}
Expected answer: {expected_answer}

JSON response:"""

        return await self._chat_completion(system_prompt, user_prompt)

    async def _chat_completion(
        self, system_prompt: str, user_prompt: str, max_retries: int = 3
    ) -> dict[str, Any]:
        """
        Make a chat completion request via OpenAI SDK to OpenRouter.
        Retries on failure (openrouter/free can route to bad models sometimes).

        Returns:
            Parsed JSON response or error dict
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        extra_body = {}
        if self.enable_reasoning:
            extra_body["reasoning"] = {"enabled": True}

        content = None
        last_error = None
        total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=2000,
                    extra_body=extra_body if extra_body else None,
                )

                content = response.choices[0].message.content
                model_used = getattr(response, "model", self.model)

                # Extract token usage
                usage = getattr(response, "usage", None)
                token_usage = {
                    "prompt_tokens": getattr(usage, "prompt_tokens", 0) if usage else 0,
                    "completion_tokens": getattr(usage, "completion_tokens", 0) if usage else 0,
                    "total_tokens": getattr(usage, "total_tokens", 0) if usage else 0,
                }
                # Accumulate usage across retries
                for k in total_usage:
                    total_usage[k] += token_usage[k]

                logger.info(
                    f"OpenRouter response | model: {model_used} | "
                    f"tokens: {token_usage['prompt_tokens']}+{token_usage['completion_tokens']}="
                    f"{token_usage['total_tokens']} | attempt: {attempt + 1}/{max_retries}"
                )

                # Handle None content - retry
                if content is None:
                    logger.warning(f"Empty response from {model_used}, retrying...")
                    last_error = f"Empty response from model {model_used}"
                    continue

                # Check for non-JSON responses (content safety models, etc.) - retry
                if "{" not in content and attempt < max_retries - 1:
                    logger.warning(f"Non-JSON response from {model_used}, retrying...")
                    last_error = f"Non-JSON response from {model_used}"
                    continue

                # Include reasoning details if available
                reasoning_details = getattr(response.choices[0].message, "reasoning_details", None)

                # Extract JSON from response
                json_content = self._extract_json(content)
                result = self._parse_json_response(json_content)

                # Attach metadata with model and usage info
                result["_meta"] = {
                    "model": model_used,
                    "model_requested": self.model,
                    "reasoning_enabled": self.enable_reasoning,
                    "usage": total_usage,
                    "attempts": attempt + 1,
                }
                if reasoning_details:
                    result["_meta"]["reasoning_details"] = reasoning_details

                return result

            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse failed (attempt {attempt + 1}): {e}")
                last_error = f"Invalid JSON response: {e}"
                if attempt == max_retries - 1:
                    return {"error": "Invalid JSON response", "raw_content": content or "", "usage": total_usage}
            except Exception as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                last_error = str(e)
                if attempt == max_retries - 1:
                    return {"error": last_error, "usage": total_usage}

        return {"error": last_error or "Max retries exceeded", "usage": total_usage}

    def _extract_json(self, content: str) -> str:
        """Extract JSON from response, handling markdown blocks and prose."""
        # Handle markdown code blocks
        if "```json" in content:
            return content.split("```json")[1].split("```")[0].strip()
        if "```" in content:
            parts = content.split("```")
            if len(parts) >= 2:
                return parts[1].strip()

        # Find JSON object in response (model may add explanation before/after)
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            return content[start:end + 1]

        return content.strip()

    def _parse_json_response(self, content: str) -> dict[str, Any]:
        """Parse JSON response, attempting to repair truncated responses."""
        if not content:
            raise json.JSONDecodeError("Empty content", "", 0)

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to repair truncated JSON by closing open structures
            repaired = content.rstrip()

            # Count open brackets/braces
            open_brackets = repaired.count("[") - repaired.count("]")
            open_braces = repaired.count("{") - repaired.count("}")

            # If no JSON structure found, raise
            if open_braces <= 0 and "{" not in repaired:
                raise

            # Truncate at last complete value if in the middle of a string
            if repaired.count('"') % 2 == 1:
                last_quote = repaired.rfind('"')
                repaired = repaired[:last_quote] + '..."'

            # Close arrays and objects
            repaired += "]" * max(0, open_brackets) + "}" * max(0, open_braces)

            logger.warning("Repaired truncated JSON response")
            return json.loads(repaired)

    async def health_check(self, max_retries: int = 3) -> dict[str, Any]:
        """Test the OpenRouter connection with a simple request. Retries on failure."""
        total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        last_error = None
        last_model = None

        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": 'Respond with exactly: {"status": "ok"}'}
                    ],
                    temperature=0,
                    max_tokens=50,
                )
                content = response.choices[0].message.content
                model_used = getattr(response, "model", self.model)
                last_model = model_used

                # Extract token usage
                usage = getattr(response, "usage", None)
                token_usage = {
                    "prompt_tokens": getattr(usage, "prompt_tokens", 0) if usage else 0,
                    "completion_tokens": getattr(usage, "completion_tokens", 0) if usage else 0,
                    "total_tokens": getattr(usage, "total_tokens", 0) if usage else 0,
                }
                for k in total_usage:
                    total_usage[k] += token_usage[k]

                logger.info(f"Health check | model: {model_used} | attempt: {attempt + 1}/{max_retries}")

                # Handle None content - retry
                if content is None:
                    logger.warning(f"Empty response from {model_used}, retrying...")
                    last_error = f"Empty response from {model_used}"
                    continue

                # Try to parse the response
                try:
                    if "{" in content:
                        json_str = content[content.index("{"):content.rindex("}") + 1]
                        result = json.loads(json_str)
                    else:
                        result = {"raw": content}
                except Exception:
                    result = {"raw": content}

                is_healthy = result.get("status") == "ok" or (content and "ok" in content.lower())

                if is_healthy:
                    logger.info(f"Health check PASSED | model: {model_used}")
                    return {
                        "healthy": True,
                        "model": model_used,
                        "model_requested": self.model,
                        "usage": total_usage,
                        "attempts": attempt + 1,
                        "response": result,
                    }
                else:
                    logger.warning(f"Unexpected response from {model_used}: {content[:100]}")
                    last_error = f"Unexpected response from {model_used}"
                    continue

            except Exception as e:
                logger.warning(f"Health check failed (attempt {attempt + 1}): {e}")
                last_error = str(e)

        return {
            "healthy": False,
            "error": last_error or "Max retries exceeded",
            "model": last_model,
            "usage": total_usage,
        }
