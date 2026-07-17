from app.models.item import Item
from app.repositories.item_repository import ItemRepository


class ItemService:
    """Business-logic layer for item lookup, crafting trees, and requirement aggregation."""

    def __init__(self, repository: ItemRepository) -> None:
        self._repository = repository

    def search(self, text: str) -> list[dict]:
        return [
            {"id": result.game_id, "name": result.name}
            for result in self._repository.search(text)
        ]

    def get_item(self, game_id: int) -> dict:
        return self._repository.get_or_fetch(game_id).to_dict()

    def get_tree(self, game_id: int) -> dict:
        item = self._repository.get_or_fetch(game_id)
        return self.build_tree(item, quantity=1)

    def get_requirements(
        self, game_id: int, quantity: int = 1, buy_ids: set[int] | None = None
    ) -> dict:
        item = self._repository.get_or_fetch(game_id)
        totals: dict[int, dict] = {}
        self.accumulate_requirements(totals, item, quantity, buy_ids)
        return {"requirements": list(totals.values())}

    def accumulate_requirements(
        self,
        totals: dict[int, dict],
        item: Item,
        quantity: int,
        buy_ids: set[int] | None = None,
    ) -> None:
        """Recursively walk `item`'s crafting tree, adding `quantity` leaf requirements into `totals`
        (keyed by game item id). Shared with ListService so a whole list can be aggregated into one dict.

        `buy_ids` lets a caller stop decomposition early at specific items (game ids) - e.g. the
        user chose to buy/gather that item directly instead of crafting it - even though it has
        a recipe and would otherwise keep decomposing."""
        buy_ids = buy_ids or set()
        if item.is_leaf() or item.game_id in buy_ids:
            entry = totals.setdefault(item.game_id, {**item.to_dict(), "quantity": 0})
            entry["quantity"] += quantity
            return

        for component in item.components:
            self.accumulate_requirements(
                totals, component.component, quantity * component.quantity, buy_ids
            )

    def build_tree(self, item: Item, quantity: int) -> dict:
        return {
            **item.to_dict(),
            "quantity": quantity,
            "children": [
                self.build_tree(component.component, component.quantity)
                for component in item.components
            ],
        }
