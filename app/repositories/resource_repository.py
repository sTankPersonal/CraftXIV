from dataclasses import dataclass

from sqlalchemy.orm import scoped_session

from app.datasources.base import DataSource
from app.extensions import db
from app.models.resource import CachedResource


@dataclass(frozen=True)
class ResourceLookupResult:
    resource: CachedResource
    from_cache: bool


class ResourceRepository:
    """Cache-aside repository: Postgres is checked first, the DataSource is the fallback."""

    def __init__(self, data_source: DataSource, session: scoped_session | None = None) -> None:
        self._data_source = data_source
        self._session = session or db.session

    def get(self, key: str) -> ResourceLookupResult:
        existing = self._session.query(CachedResource).filter_by(key=key).one_or_none()
        if existing is not None:
            return ResourceLookupResult(resource=existing, from_cache=True)

        return ResourceLookupResult(resource=self._fetch_and_store(key), from_cache=False)

    def _fetch_and_store(self, key: str) -> CachedResource:
        payload = self._data_source.fetch(key)

        resource = CachedResource(key=key, payload=payload)
        self._session.add(resource)
        self._session.commit()

        return resource
