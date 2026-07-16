from dataclasses import dataclass, field

from app.datasources.ingredient_ref import IngredientRef
from app.models.acquisition_type import AcquisitionType


@dataclass(frozen=True)
class ParsedItem:
    """Normalized item data as returned by an ItemDataSource, independent of any ORM model."""

    game_id: int
    name: str
    icon_id: int | None
    ilvl: int | None
    category: int | None
    acquisition_type: AcquisitionType
    vendor_price: int | None = None
    gathering_node_ids: list[int] | None = None
    ingredients: list[IngredientRef] = field(default_factory=list)
    raw_payload: dict | None = None
