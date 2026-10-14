"""Tolerant JSON parsing for LLM responses.

Wraps langchain_core's parse_json_markdown / parse_partial_json, which strip markdown
fences and repair truncated JSON — closing unterminated strings and nested structures
in the correct order, which naive bracket-counting gets wrong.

Two gaps in langchain are covered here:
  - it only recognises a lowercase ```json fence (langchain-ai/langchain#40297)
  - it fails outright when the model wraps the JSON in prose
"""
import json
import re
from typing import Any

from langchain_core.utils.json import parse_json_markdown

try:
    # When running as part of src package (FastAPI)
    from ..utils.logger import get_logger
except ImportError:
    # When running standalone (tox/pytest with PYTHONPATH=src)
    from utils.logger import get_logger

logger = get_logger(name=__name__)

_JSON_FENCE = re.compile(r"```[ \t]*json\b", re.IGNORECASE)


def parse_json_response(content: str) -> dict[str, Any]:
    """Parse JSON out of an LLM response, tolerating fences, prose and truncation."""
    if not content:
        raise json.JSONDecodeError("Empty content", "", 0)

    normalised = _JSON_FENCE.sub("```json", content)

    try:
        return parse_json_markdown(normalised)
    except json.JSONDecodeError:
        start = normalised.find("{")
        if start == -1:
            raise
        end = normalised.rfind("}")
        sliced = normalised[start:end + 1] if end > start else normalised[start:]
        logger.warning("JSON embedded in prose; sliced before parsing")
        return parse_json_markdown(sliced)
