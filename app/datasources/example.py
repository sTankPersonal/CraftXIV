from datetime import datetime, timezone

from app.datasources.base import DataSource


class ExampleDataSource(DataSource):
    """Placeholder DataSource implementation.

    Demonstrates the shape a real external API client should have, without
    depending on any third-party service being reachable/reliable. Swap this
    out (or add a sibling class using `requests`/an SDK) for whichever
    concrete API CraftXIV ends up integrating with; nothing else in the app
    needs to change as long as the replacement also implements `DataSource`.
    """

    def fetch(self, key: str) -> dict:
        return {
            "key": key,
            "origin": "ExampleDataSource",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
