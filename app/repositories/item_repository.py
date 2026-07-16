from sqlalchemy.orm import scoped_session

from app.datasources.base import ItemDataSource
from app.datasources.search_result import SearchResult
from app.extensions import db
from app.models.acquisition_type import AcquisitionType
from app.models.item import Item
from app.models.item_component import ItemComponent


class ItemRepository:
    """Cache-aside repository for items. Postgres is checked first; on a miss, the ItemDataSource
    is called and the result (plus, recursively, every crafting ingredient) is persisted."""

    def __init__(self, data_source: ItemDataSource, session: scoped_session | None = None) -> None:
        self._data_source = data_source
        self._session = session or db.session

    def get_or_fetch(self, game_id: int, visiting: set[int] | None = None) -> Item:
        existing = self._session.query(Item).filter_by(game_id=game_id).one_or_none()
        if existing is not None:
            return existing

        visiting = visiting if visiting is not None else set()
        if game_id in visiting:
            raise ValueError(f"Cycle detected while resolving item {game_id}")
        visiting.add(game_id)

        return self._fetch_and_store(game_id, visiting)

    def search(self, text: str) -> list[SearchResult]:
        return self._data_source.search(text)

    def _fetch_and_store(self, game_id: int, visiting: set[int]) -> Item:
        parsed = self._data_source.fetch_item(game_id)

        item = Item(
            game_id=parsed.game_id,
            name=parsed.name,
            icon_id=parsed.icon_id,
            ilvl=parsed.ilvl,
            category=parsed.category,
            acquisition_type=parsed.acquisition_type.value
            if isinstance(parsed.acquisition_type, AcquisitionType)
            else parsed.acquisition_type,
            vendor_price=parsed.vendor_price,
            gathering_node_ids=parsed.gathering_node_ids,
            raw_payload=parsed.raw_payload,
        )
        self._session.add(item)
        self._session.flush()

        for ingredient in parsed.ingredients:
            component_item = self.get_or_fetch(ingredient.game_id, visiting)
            self._session.add(
                ItemComponent(
                    parent_item_id=item.id,
                    component_item_id=component_item.id,
                    quantity=ingredient.amount,
                )
            )

        self._session.commit()
        return item
