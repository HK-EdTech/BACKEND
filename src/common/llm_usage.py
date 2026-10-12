"""Token usage accounting shared by the agent graph.

LangChain reports usage as input_tokens/output_tokens; the rest of this repo (and
OpenRouterLLM before it) uses the OpenAI names prompt_tokens/completion_tokens.
Everything is normalised to the repo's names here.

`add_usage` is a LangGraph state reducer: nodes return a *delta* and LangGraph folds
it in, which is what makes usage survive parallel branches. Mutating a plain channel
raises InvalidUpdateError when two branches write at once.
"""
from __future__ import annotations

from typing import Any

EMPTY_USAGE: dict[str, int] = {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0,
}

_KEYS = tuple(EMPTY_USAGE)


def add_usage(left: dict | None, right: dict | None) -> dict[str, int]:
    """Reducer: sum two usage dicts, tolerating None on either side."""
    left = left or EMPTY_USAGE
    right = right or EMPTY_USAGE
    return {key: int(left.get(key, 0)) + int(right.get(key, 0)) for key in _KEYS}


def usage_from_ai_message(message: Any) -> dict[str, int]:
    """Pull usage off a LangChain AIMessage, defensively.

    Providers routed through OpenRouter do not all populate usage, and the structured
    output path can hand back objects without it, so every access is guarded.
    """
    metadata = getattr(message, "usage_metadata", None)
    if metadata:
        return {
            "prompt_tokens": int(metadata.get("input_tokens", 0) or 0),
            "completion_tokens": int(metadata.get("output_tokens", 0) or 0),
            "total_tokens": int(metadata.get("total_tokens", 0) or 0),
        }

    response_metadata = getattr(message, "response_metadata", None) or {}
    token_usage = response_metadata.get("token_usage") or {}
    if token_usage:
        return {key: int(token_usage.get(key, 0) or 0) for key in _KEYS}

    return dict(EMPTY_USAGE)


def model_from_ai_message(message: Any, fallback: str) -> str:
    """Which model actually answered — OpenRouter may route elsewhere than requested."""
    response_metadata = getattr(message, "response_metadata", None) or {}
    return response_metadata.get("model_name") or response_metadata.get("model") or fallback
