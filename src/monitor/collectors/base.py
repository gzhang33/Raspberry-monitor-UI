"""Base class for all metric collectors."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseCollector(ABC):
    """Abstract base class for metric collectors.

    All collectors must implement the collect() method and provide a name.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Collector name for logging and identification."""
        pass

    @abstractmethod
    def collect(self) -> Dict[str, Any]:
        """Collect and return metrics.

        Returns:
            Dictionary of metric names to values.
            Should return empty dict on error rather than raising.
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
