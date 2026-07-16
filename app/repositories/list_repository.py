from sqlalchemy.orm import scoped_session

from app.extensions import db
from app.models.crafting_list import CraftingList
from app.models.crafting_list_item import CraftingListItem
from app.models.item import Item


class ListRepository:
    """CRUD persistence for CraftingList/CraftingListItem, always scoped to an owning user."""

    def __init__(self, session: scoped_session | None = None) -> None:
        self._session = session or db.session

    def list_for_user(self, user_id: int) -> list[CraftingList]:
        return self._session.query(CraftingList).filter_by(user_id=user_id).all()

    def get_list(self, list_id: int, user_id: int) -> CraftingList | None:
        return (
            self._session.query(CraftingList)
            .filter_by(id=list_id, user_id=user_id)
            .one_or_none()
        )

    def create_list(self, user_id: int, name: str) -> CraftingList:
        crafting_list = CraftingList(user_id=user_id, name=name)
        self._session.add(crafting_list)
        self._session.commit()
        return crafting_list

    def rename_list(self, crafting_list: CraftingList, name: str) -> CraftingList:
        crafting_list.name = name
        self._session.commit()
        return crafting_list

    def delete_list(self, crafting_list: CraftingList) -> None:
        self._session.delete(crafting_list)
        self._session.commit()

    def get_list_item(self, list_id: int, list_item_id: int) -> CraftingListItem | None:
        return (
            self._session.query(CraftingListItem)
            .filter_by(id=list_item_id, list_id=list_id)
            .one_or_none()
        )

    def add_item(self, crafting_list: CraftingList, item: Item, quantity: int) -> CraftingListItem:
        list_item = CraftingListItem(list_id=crafting_list.id, item_id=item.id, quantity=quantity)
        self._session.add(list_item)
        self._session.commit()
        return list_item

    def update_item_quantity(self, list_item: CraftingListItem, quantity: int) -> CraftingListItem:
        list_item.quantity = quantity
        self._session.commit()
        return list_item

    def remove_item(self, list_item: CraftingListItem) -> None:
        self._session.delete(list_item)
        self._session.commit()
