from dataclasses import dataclass, field

from app.models.acquisition_type import AcquisitionType


@dataclass(frozen=True)
class ParsedAcquisition:
    """A single normalized way to obtain an item (one gathering node, one vendor NPC, one
    drop source, one trade shop listing, ...), independent of any ORM model.

    `ref_id` is whatever id identifies the source for this acquisition type (node id, NPC id,
    mob id, treasure map item id, leve id, venture id, voyage id, or source item id for
    desynthesis) - it has no meaning on its own without `acquisition_type`.

    `details` holds whatever extra fields are specific to this acquisition type (e.g. `stars`
    and `time_windows` for GATHER, `price` for VENDOR, `listings` for TRADE_SHOP, `seals` for
    SUPPLY). Keeping these in a free-form dict instead of dedicated columns per type means
    adding a new acquisition type never requires a schema change.
    """

    acquisition_type: AcquisitionType
    location_name: str | None = None
    zone_id: int | None = None
    zone_name: str | None = None
    coords_x: float | None = None
    coords_y: float | None = None
    ref_id: int | None = None
    details: dict = field(default_factory=dict)
