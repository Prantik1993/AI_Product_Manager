"""Abstract base class for all agents."""

from abc import ABC, abstractmethod
from typing import Dict, Any

from src.monitoring.logger import get_logger


class BaseAgent(ABC):
    """
    Base class providing a structured logger per agent.
    Use self.logger directly — it supports full structured logging (extra, exc_info, etc.)
    """

    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"agent.{name}")

    @abstractmethod
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's analysis. Must be implemented by subclasses."""
        pass
