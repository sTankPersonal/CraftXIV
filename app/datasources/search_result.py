from dataclasses import dataclass


@dataclass(frozen=True)
class SearchResult:
    """A single item search hit."""

    game_id: int
    name: str
