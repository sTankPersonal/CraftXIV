from abc import ABC, abstractmethod

from app.datasources.parsed_item import ParsedItem
from app.datasources.search_result import SearchResult


class ItemDataSource(ABC):
    """Interface for any external system that can look up FFXIV item data."""

    @abstractmethod
    def fetch_item(self, game_id: int) -> ParsedItem:
        """Fetch full item data (including its direct crafting ingredients, if any) for `game_id`."""
        raise NotImplementedError

    @abstractmethod
    def search(self, text: str) -> list[SearchResult]:
        """Search for items by name. Not cached — always a live call."""
        raise NotImplementedError
