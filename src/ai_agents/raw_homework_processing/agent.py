"""Agent entry point reserved for the redesigned raw homework workflow."""
from typing import Any, Callable

try:
    from ...common.images import ImageBundle
    from ..llm import Tier, make_llm_factory
except ImportError:
    from common.images import ImageBundle
    from ai_agents.llm import Tier, make_llm_factory


class WorkflowNotImplementedError(NotImplementedError):
    """The previous graph has been removed; its replacement is not defined yet."""


class RawHomeworkProcessingAgent:
    def __init__(self, llm_factory: Callable[[Tier], Any] | None = None,
                 api_key: str | None = None) -> None:
        if llm_factory is None:
            if not api_key:
                raise ValueError("Either llm_factory or api_key is required")
            llm_factory = make_llm_factory(api_key)
        self.llm_factory = llm_factory

    async def run(self, bundle: ImageBundle,
                  extra_information: str | None = None) -> dict:
        raise WorkflowNotImplementedError(
            "Raw homework processing is awaiting a new graph definition."
        )
