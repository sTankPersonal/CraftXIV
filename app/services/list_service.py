from app.repositories.item_repository import ItemRepository
from app.repositories.list_repository import ListRepository
from app.services.item_service import ItemService


class ListService:
    """Business-logic layer for CRUD on a user's crafting lists and their items."""

    def __init__(
        self,
        list_repository: ListRepository,
        item_repository: ItemRepository,
        item_service: ItemService,
    ) -> None:
        self._list_repository = list_repository
        self._item_repository = item_repository
        self._item_service = item_service

    def get_lists(self, user_id: int) -> list[dict]:
        return [crafting_list.to_dict() for crafting_list in self._list_repository.list_for_user(user_id)]

    def create_list(self, user_id: int, name: str) -> dict:
        return self._list_repository.create_list(user_id, name).to_dict()

    def get_list(self, list_id: int, user_id: int) -> dict | None:
        crafting_list = self._list_repository.get_list(list_id, user_id)
        if crafting_list is None:
            return None
        return {**crafting_list.to_dict(), "items": [item.to_dict() for item in crafting_list.items]}

    def rename_list(self, list_id: int, user_id: int, name: str) -> dict | None:
        crafting_list = self._list_repository.get_list(list_id, user_id)
        if crafting_list is None:
            return None
        return self._list_repository.rename_list(crafting_list, name).to_dict()

    def delete_list(self, list_id: int, user_id: int) -> bool:
        crafting_list = self._list_repository.get_list(list_id, user_id)
        if crafting_list is None:
            return False
        self._list_repository.delete_list(crafting_list)
        return True

    def add_item(self, list_id: int, user_id: int, game_id: int, quantity: int) -> dict | None:
        crafting_list = self._list_repository.get_list(list_id, user_id)
        if crafting_list is None:
            return None
        item = self._item_repository.get_or_fetch(game_id)
        return self._list_repository.add_item(crafting_list, item, quantity).to_dict()

    def update_item_quantity(
        self, list_id: int, user_id: int, list_item_id: int, quantity: int
    ) -> dict | None:
        crafting_list = self._list_repository.get_list(list_id, user_id)
        if crafting_list is None:
            return None
        list_item = self._list_repository.get_list_item(list_id, list_item_id)
        if list_item is None:
            return None
        return self._list_repository.update_item_quantity(list_item, quantity).to_dict()

    def remove_item(self, list_id: int, user_id: int, list_item_id: int) -> bool:
        crafting_list = self._list_repository.get_list(list_id, user_id)
        if crafting_list is None:
            return False
        list_item = self._list_repository.get_list_item(list_id, list_item_id)
        if list_item is None:
            return False
        self._list_repository.remove_item(list_item)
        return True

    def get_list_requirements(self, list_id: int, user_id: int) -> dict | None:
        crafting_list = self._list_repository.get_list(list_id, user_id)
        if crafting_list is None:
            return None

        totals: dict[int, dict] = {}
        for list_item in crafting_list.items:
            self._item_service.accumulate_requirements(totals, list_item.item, list_item.quantity)
        return {"requirements": list(totals.values())}
