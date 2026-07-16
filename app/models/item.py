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
    acquisition_type = db.Column(db.String(20), nullable=False)
    vendor_price = db.Column(db.Integer, nullable=True)
    gathering_node_ids = db.Column(db.JSON, nullable=True)
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

    def is_leaf(self) -> bool:
        return self.acquisition_type != AcquisitionType.CRAFT.value

    def to_dict(self) -> dict:
        return {
            "id": self.game_id,
            "name": self.name,
            "icon_id": self.icon_id,
            "ilvl": self.ilvl,
            "category": self.category,
            "acquisition_type": self.acquisition_type,
            "vendor_price": self.vendor_price,
            "gathering_node_ids": self.gathering_node_ids,
        }
