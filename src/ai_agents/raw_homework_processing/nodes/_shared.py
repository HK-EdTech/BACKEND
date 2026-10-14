"""Helpers every node uses.

The image bundle and the LLM factory arrive through config["configurable"], never
through state: LangGraph passes config by reference and never serialises it, so no
base64 is ever copied between supersteps or written to a checkpoint.
"""
from __future__ import annotations

from langchain_core.runnables import RunnableConfig

try:
    from ....common.images import ImageBundle
except ImportError:
    from common.images import ImageBundle


def get_bundle(config: RunnableConfig) -> ImageBundle:
    bundle = (config.get("configurable") or {}).get("image_bundle")
    if bundle is None:
        raise RuntimeError("image_bundle missing from graph config")
    return bundle


def get_llm(config: RunnableConfig, tier: str):
    factory = (config.get("configurable") or {}).get("llms")
    if factory is None:
        raise RuntimeError("llms factory missing from graph config")
    return factory(tier)

