from app.repositories.resource_repository import ResourceRepository


class ResourceService:
    """Business-logic layer sitting between routes and the repository."""

    def __init__(self, repository: ResourceRepository) -> None:
        self._repository = repository

    def get_resource(self, key: str) -> dict:
        result = self._repository.get(key)
        return {
            "source": "cache" if result.from_cache else "origin",
            **result.resource.to_dict(),
        }
