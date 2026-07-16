from app.extensions import db
from app.models.acquisition_type import AcquisitionType


class ItemAcquisition(db.Model):
    """A single way to obtain an item: one gathering node or one vendor NPC selling it.

    An item with a craft recipe (see ItemComponent) has no rows here unless it can *also*
    be gathered or bought directly.
    """

    __tablename__ = "item_acquisitions"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False, index=True)
    acquisition_type = db.Column(db.String(20), nullable=False)

    location_name = db.Column(db.String(255), nullable=True)
    zone_id = db.Column(db.Integer, nullable=True)
    coords_x = db.Column(db.Float, nullable=True)
    coords_y = db.Column(db.Float, nullable=True)

    # Gather-specific
    node_id = db.Column(db.Integer, nullable=True)
    gathering_type = db.Column(db.Integer, nullable=True)
    stars = db.Column(db.Integer, nullable=True)
    limit_type = db.Column(db.String(20), nullable=True)
    time_windows = db.Column(db.JSON, nullable=True)
    uptime_minutes = db.Column(db.Integer, nullable=True)

    # Vendor-specific
    npc_id = db.Column(db.Integer, nullable=True)
    price = db.Column(db.Integer, nullable=True)

    item = db.relationship("Item", back_populates="acquisitions")

    def to_dict(self) -> dict:
        base = {
            "id": self.id,
            "acquisition_type": self.acquisition_type,
            "location_name": self.location_name,
            "zone_id": self.zone_id,
            "coords": [self.coords_x, self.coords_y] if self.coords_x is not None else None,
        }
        if self.acquisition_type == AcquisitionType.GATHER.value:
            base.update(
                {
                    "node_id": self.node_id,
                    "gathering_type": self.gathering_type,
                    "stars": self.stars,
                    "limit_type": self.limit_type,
                    "time_windows": self.time_windows,
                    "uptime_minutes": self.uptime_minutes,
                }
            )
        elif self.acquisition_type == AcquisitionType.VENDOR.value:
            base.update({"npc_id": self.npc_id, "price": self.price})
        return base
