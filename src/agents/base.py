from abc import ABC, abstractmethod
from typing import Dict, Any
from src.utils.logger import get_logger  # <--- NEW: Enterprise Logger

class BaseAgent(ABC):
    """
    Abstract Base Class for all agents in the system.
    Enforces structure and provides standardized logging.
    """
    def __init__(self, name: str):
        self.name = name
        # Initialize structured logger for this specific agent
        self.logger = get_logger(f"agent.{name}")

    def log(self, message: str):
        """Log a message with the agent's structured logger."""
        self.logger.info(message)

    def log_error(self, message: str):
        """Log an error message."""
        self.logger.error(message)

    @abstractmethod
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's logic.
        Must be implemented by subclasses.
        """
        pass