from datetime import datetime, timezone

from app.extensions import db
from app.models.acquisition_type import AcquisitionType


class Item(db.Model):
    """A game item cached from the external item DataSource (e.g. Garland Tools)."""

    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    icon_id = db.Column(db.Integer, nullable=True)
    ilvl = db.Column(db.Integer, nullable=True)
    category = db.Column(db.Integer, nullable=True)
    raw_payload = db.Column(db.JSON, nullable=True)
    fetched_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    components = db.relationship(
        "ItemComponent",
        foreign_keys="ItemComponent.parent_item_id",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    acquisitions = db.relationship(
        "ItemAcquisition", back_populates="item", cascade="all, delete-orphan"
    )

    def is_leaf(self) -> bool:
        """An item is a leaf (a raw material to buy/gather rather than craft) if it has no
        recipe, or if it has a recipe but can *also* be gathered or bought directly."""
        return not self.components or bool(self.acquisitions)

    def acquisition_types(self) -> list[str]:
        """All the ways this item can be obtained - not just one. An item can be both craftable
        *and* buyable/gatherable/etc, and callers need to see every option, not just the first
        one found."""
        types = {acquisition.acquisition_type for acquisition in self.acquisitions}
        if self.components:
            types.add(AcquisitionType.CRAFT.value)
        return sorted(types) if types else [AcquisitionType.UNKNOWN.value]

    def to_dict(self) -> dict:
        return {
            "id": self.game_id,
            "name": self.name,
            "icon_id": self.icon_id,
            "ilvl": self.ilvl,
            "category": self.category,
            "acquisition_types": self.acquisition_types(),
            "acquisitions": [acquisition.to_dict() for acquisition in self.acquisitions],
        }
