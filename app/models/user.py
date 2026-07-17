from datetime import datetime, timezone

from flask_login import UserMixin

from app.extensions import db


class User(db.Model, UserMixin):
    """An application user, identified by an OAuth provider identity."""

    __tablename__ = "users"
    __table_args__ = (db.UniqueConstraint("provider", "provider_user_id", name="uq_user_provider_identity"),)

    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(20), nullable=False)
    provider_user_id = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "display_name": self.display_name,
        }
