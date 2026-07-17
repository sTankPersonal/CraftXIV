from app.extensions import db
from app.models.acquisition_type import AcquisitionType


def _lines(*values: str | None) -> list[str]:
    return [value for value in values if value]


def _describe_entries(entries: list[dict]) -> str:
    return ", ".join(f"{entry['amount']}x {entry.get('name') or entry['id']}" for entry in entries)


def _is_timed_gather(details: dict) -> bool:
    # "limited" is the authoritative flag (set from Garland's own `limited` boolean), but fall
    # back to inferring it for rows persisted before that field existed.
    return bool(details.get("limited") or details.get("limit_type") or details.get("time_windows"))


def _gather_lines(details: dict) -> list[str]:
    limit_type = details.get("limit_type")
    time_windows = details.get("time_windows")
    is_timed = _is_timed_gather(details)
    return _lines(
        f"Timed gather ({limit_type})" if limit_type else ("Timed gather" if is_timed else None),
        f"Up at hour(s) {', '.join(str(hour) for hour in time_windows)}" if time_windows else None,
        f"{details['uptime_minutes']}m uptime" if details.get("uptime_minutes") else None,
    )


def _vendor_lines(details: dict) -> list[str]:
    return _lines(f"{details['price']} gil" if details.get("price") else None)


def _trade_shop_lines(details: dict) -> list[str]:
    return [
        f"{_describe_entries(listing['cost'])} → {_describe_entries(listing['receive'])}"
        for listing in details.get("listings", [])
        if listing.get("cost") and listing.get("receive")
    ]


def _leve_lines(details: dict) -> list[str]:
    return _lines(f"Lv. {details['level']} levequest" if details.get("level") else None)


def _drop_lines(details: dict) -> list[str]:
    return _lines(f"Mob level {details['level']}" if details.get("level") else None)


def _voyage_lines(details: dict) -> list[str]:
    voyage_type = details.get("voyage_type")
    return _lines(f"Voyage (type {voyage_type})" if voyage_type is not None else None)


def _supply_lines(details: dict) -> list[str]:
    return _lines(
        f"{details['seals']} GC seals" if details.get("seals") else None,
        f"{details['xp']} XP" if details.get("xp") else None,
    )


# One formatter per acquisition type that has extra details worth surfacing. Types missing here
# (desynth, treasure, venture) render with no extra lines - just the location/name and badge.
# Adding a 12th acquisition type only means adding an entry here; the template never changes.
_DETAIL_LINE_FORMATTERS = {
    AcquisitionType.GATHER.value: _gather_lines,
    AcquisitionType.VENDOR.value: _vendor_lines,
    AcquisitionType.TRADE_SHOP.value: _trade_shop_lines,
    AcquisitionType.LEVE.value: _leve_lines,
    AcquisitionType.DROP.value: _drop_lines,
    AcquisitionType.VOYAGE.value: _voyage_lines,
    AcquisitionType.SUPPLY.value: _supply_lines,
}


class ItemAcquisition(db.Model):
    """A single way to obtain an item: one gathering node, one vendor NPC, one trade shop
    listing, one drop source, etc. - see AcquisitionType for the full set.

    An item with a craft recipe (see ItemComponent) has no rows here unless it can *also*
    be obtained directly by one of these other methods.
    """

    __tablename__ = "item_acquisitions"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False, index=True)
    acquisition_type = db.Column(db.String(20), nullable=False)

    location_name = db.Column(db.String(255), nullable=True)
    zone_id = db.Column(db.Integer, nullable=True)
    zone_name = db.Column(db.String(255), nullable=True)
    coords_x = db.Column(db.Float, nullable=True)
    coords_y = db.Column(db.Float, nullable=True)

    # The id of whatever this acquisition points at: a gathering node, an NPC (vendor or trade
    # shop), a mob (drop), a treasure map item, a leve, a venture, a voyage, or a source item
    # (desynthesis). BigInteger because mob ids run well past 32-bit range (e.g. 170000002743).
    ref_id = db.Column(db.BigInteger, nullable=True)

    # Type-specific extras that don't belong on every row (stars/time windows for gather, price
    # for vendor, currency listings for trade shop, seals/xp for supply, ...). Keeping these in
    # one JSON column instead of a dedicated nullable column per type means a new acquisition
    # type never requires a migration for its own fields.
    details = db.Column(db.JSON, nullable=True)

    item = db.relationship("Item", back_populates="acquisitions")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "acquisition_type": self.acquisition_type,
            "location_name": self.location_name,
            "zone_id": self.zone_id,
            "zone_name": self.zone_name,
            "coords": [self.coords_x, self.coords_y] if self.coords_x is not None else None,
            "ref_id": self.ref_id,
            "detail_lines": self.detail_lines(),
            "is_timed": self.is_timed(),
            **(self.details or {}),
        }

    def detail_lines(self) -> list[str]:
        """Human-readable extra lines for this acquisition (e.g. "1,200 gil", "Up at hour(s)
        4, 5"). Dispatched by acquisition_type so callers (templates included) never need a
        per-type branch."""
        formatter = _DETAIL_LINE_FORMATTERS.get(self.acquisition_type)
        return formatter(self.details or {}) if formatter else []

    def is_timed(self) -> bool:
        """Whether this acquisition is only available on a schedule (a timed/Unspoiled/
        Ephemeral/Legendary gathering node), so the type badge can flag it before the user
        opens the dropdown - not just inside it."""
        return self.acquisition_type == AcquisitionType.GATHER.value and _is_timed_gather(
            self.details or {}
        )
