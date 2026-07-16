from datetime import datetime, timezone

from app.extensions import db


class CraftingListItem(db.Model):
    """A quantity of a single item that a user has added to one of their crafting lists."""

    __tablename__ = "crafting_list_items"

    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey("crafting_lists.id"), nullable=False, index=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    list = db.relationship("CraftingList", back_populates="items")
    item = db.relationship("Item")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "item": self.item.to_dict(),
            "quantity": self.quantity,
        }
