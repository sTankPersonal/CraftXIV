from datetime import datetime, timezone

from app.extensions import db


class CachedResource(db.Model):
    """A piece of data fetched from an external DataSource and cached in Postgres."""

    __tablename__ = "cached_resources"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), unique=True, nullable=False, index=True)
    payload = db.Column(db.JSON, nullable=False)
    fetched_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "payload": self.payload,
            "fetched_at": self.fetched_at.isoformat(),
        }
