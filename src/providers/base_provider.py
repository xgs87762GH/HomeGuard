from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseProvider(ABC):
    """Base class for all providers"""

    def __init__(self):
        self.name: str = "base_provider"
        self.config: Dict[str, Any] = {}
        self.enabled: bool = True

    @abstractmethod
    async def get_capabilities(self) -> List[str]:
        """Get list of capabilities this provider supports"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is healthy and operational"""
        pass

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"

    def __repr__(self) -> str:
        return self.__str__()