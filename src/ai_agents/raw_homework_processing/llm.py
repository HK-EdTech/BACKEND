"""Tiered model calls with explicit text or schema-free JSON responses."""
from __future__ import annotations

from typing import Any, Callable, Literal, Protocol, TypedDict
import os

from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

try:
    from ...common.json_extract import parse_json_response
    from ...common.llm_usage import EMPTY_USAGE, add_usage, model_from_ai_message, usage_from_ai_message
except ImportError:
    from common.json_extract import parse_json_response
    from common.llm_usage import EMPTY_USAGE, add_usage, model_from_ai_message, usage_from_ai_message

ResponseFormat = Literal["text", "json"]

class NodeCall(TypedDict):
    node: str
    model: str
    model_requested: str
    response_format: ResponseFormat
    attempts: int
    usage: dict
    ok: bool
    error: str | None

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

Tier = Literal["cheap", "thinking"]

DEFAULT_CHEAP_MODEL = "qwen/qwen3-vl-32b-instruct"
# NOTE: a 30B A3B MoE has ~3B active parameters against the cheap tier's 32B dense, so
# this escalates to *reasoning*, not to capacity. Compare both before relying on it.
DEFAULT_THINKING_MODEL = "qwen/qwen3-vl-30b-a3b-thinking"



def model_for_tier(tier: Tier) -> str:
    """Env is read per call so tests and deployments can override without reimporting."""
    if tier == "thinking":
        return os.getenv("OPENROUTER_VL_THINKING_MODEL", DEFAULT_THINKING_MODEL)
    return os.getenv("OPENROUTER_VL_MODEL", DEFAULT_CHEAP_MODEL)


def build_chat_model(tier: Tier, api_key: str) -> ChatOpenAI:
    return ChatOpenAI(
        model=model_for_tier(tier),
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key,
        temperature=0.1,
        max_tokens=4000,
        timeout=180,
        max_retries=0,  # retries are handled here so usage can be accumulated
        default_headers={
            "HTTP-Referer": os.getenv("APP_URL", "http://localhost:8000"),
            "X-Title": "HK EdTech Homework Marking",
        },
        extra_body={"provider": {"require_parameters": True}},
    )



class LLMCaller(Protocol):
    async def __call__(self, messages: list[BaseMessage], node_name: str, *,
                       response_format: ResponseFormat,
                       config: RunnableConfig | None = None) -> tuple[Any, NodeCall]: ...


class OpenRouterCaller:
    """Return plain text or parsed JSON, with retries and cumulative usage.

    JSON is requested in the prompt without a schema or provider response-format
    constraint. No graph-specific interpretation or validation is performed.
    """
    def __init__(self, tier: Tier, api_key: str, max_retries: int = 3):
        if max_retries < 1:
            raise ValueError("max_retries must be at least 1")
        self.model = model_for_tier(tier)
        self.llm = build_chat_model(tier, api_key)
        self.max_retries = max_retries

    async def __call__(self, messages: list[BaseMessage], node_name: str, *,
                       response_format: ResponseFormat,
                       config: RunnableConfig | None = None) -> tuple[Any, NodeCall]:
        if response_format not in ("text", "json"):
            raise ValueError("response_format must be text or json")
        request = list(messages)
        if response_format == "json":
            request = [SystemMessage(content="Respond with valid JSON only. No fixed schema is required."), *request]
        call: NodeCall = {
            "node": node_name, "model": self.model, "model_requested": self.model,
            "response_format": response_format, "attempts": 0,
            "usage": dict(EMPTY_USAGE), "ok": False, "error": None,
        }
        for _ in range(self.max_retries):
            call["attempts"] += 1
            try:
                raw = await self.llm.ainvoke(request, config=config)
                call["usage"] = add_usage(call["usage"], usage_from_ai_message(raw))
                call["model"] = model_from_ai_message(raw, self.model)
                content = raw.content
                if isinstance(content, list):
                    content = "".join(p if isinstance(p, str) else p.get("text", "")
                                      for p in content if isinstance(p, (str, dict)))
                if not isinstance(content, str) or not content.strip():
                    raise ValueError("model returned no text content")
                result = parse_json_response(content) if response_format == "json" else content
                call.update(ok=True, error=None)
                return result, call
            except Exception as exc:
                call["error"] = f"{type(exc).__name__}: {exc}"
        return None, call


def make_llm_factory(api_key: str) -> Callable[[Tier], LLMCaller]:
    """Lazily create and reuse one caller per model tier."""
    cache: dict[Tier, LLMCaller] = {}
    def factory(tier: Tier) -> LLMCaller:
        if tier not in cache:
            cache[tier] = OpenRouterCaller(tier, api_key)
        return cache[tier]
    return factory
