from dataclasses import dataclass

from app.models.acquisition_type import AcquisitionType


@dataclass(frozen=True)
class ParsedAcquisition:
    """A single normalized way to obtain an item (one gathering node or one vendor NPC),
    independent of any ORM model."""

    acquisition_type: AcquisitionType
    location_name: str | None = None
    zone_id: int | None = None
    coords_x: float | None = None
    coords_y: float | None = None

    # Gather-specific
    node_id: int | None = None
    gathering_type: int | None = None
    stars: int | None = None
    limit_type: str | None = None
    time_windows: list[int] | None = None
    uptime_minutes: int | None = None

    # Vendor-specific
    npc_id: int | None = None
    price: int | None = None
