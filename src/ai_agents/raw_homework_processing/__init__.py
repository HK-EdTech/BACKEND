try:
    from .agent import RawHomeworkProcessingAgent
except ImportError:
    from ai_agents.raw_homework_processing.agent import RawHomeworkProcessingAgent

__all__ = ["RawHomeworkProcessingAgent"]
