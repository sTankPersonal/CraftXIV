from dataclasses import dataclass


@dataclass(frozen=True)
class IngredientRef:
    """A reference to `amount` of a component item, by its external game id."""

    game_id: int
    amount: int
