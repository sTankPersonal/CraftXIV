from app.extensions import db


class ItemComponent(db.Model):
    """A single recipe ingredient edge: `quantity` of `component_item` is needed to craft `parent_item`."""

    __tablename__ = "item_components"

    id = db.Column(db.Integer, primary_key=True)
    parent_item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False, index=True)
    component_item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False)

    parent = db.relationship("Item", foreign_keys=[parent_item_id], back_populates="components")
    component = db.relationship("Item", foreign_keys=[component_item_id])
