from abc import ABC, abstractmethod


class DataSource(ABC):
    """Interface for any external system that can produce data for a given key."""

    @abstractmethod
    def fetch(self, key: str) -> dict:
        """Fetch fresh data for `key` from the origin system. Raises on failure."""
        raise NotImplementedError
