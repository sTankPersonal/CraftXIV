from dotenv import load_dotenv

load_dotenv()

import pytest

from app.config import TestConfig
from app.datasources.base import ItemDataSource
from app.datasources.ingredient_ref import IngredientRef
from app.datasources.parsed_acquisition import ParsedAcquisition
from app.datasources.parsed_item import ParsedItem
from app.datasources.search_result import SearchResult
from app.extensions import db
from app.factory import AppFactory
from app.models.acquisition_type import AcquisitionType


class FakeItemDataSource(ItemDataSource):
    """Serves ParsedItem fixtures from memory and records which ids were fetched,
    so tests can assert whether the origin was actually hit."""

    def __init__(self, items: dict[int, ParsedItem]) -> None:
        self._items = items
        self.fetch_calls: list[int] = []

    def fetch_item(self, game_id: int) -> ParsedItem:
        self.fetch_calls.append(game_id)
        return self._items[game_id]

    def search(self, text: str) -> list[SearchResult]:
        return [
            SearchResult(game_id=item.game_id, name=item.name)
            for item in self._items.values()
            if text.lower() in item.name.lower()
        ]


@pytest.fixture
def app():
    application = AppFactory(config_object=TestConfig).create_app()

    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def fake_data_source():
    """A small crafting tree: item 1 (craft) needs 3x item 2 (gather) + 1x item 3 (vendor)."""
    return FakeItemDataSource(
        {
            1: ParsedItem(
                game_id=1,
                name="Widget",
                icon_id=None,
                ilvl=1,
                category=1,
                ingredients=[
                    IngredientRef(game_id=2, amount=3),
                    IngredientRef(game_id=3, amount=1),
                ],
            ),
            2: ParsedItem(
                game_id=2,
                name="Ore",
                icon_id=None,
                ilvl=1,
                category=1,
                acquisitions=[
                    ParsedAcquisition(
                        acquisition_type=AcquisitionType.GATHER,
                        location_name="Dragonhead",
                        node_id=100,
                    )
                ],
            ),
            3: ParsedItem(
                game_id=3,
                name="Bolt",
                icon_id=None,
                ilvl=1,
                category=1,
                acquisitions=[
                    ParsedAcquisition(
                        acquisition_type=AcquisitionType.VENDOR,
                        location_name="Jossy",
                        npc_id=200,
                        price=50,
                    )
                ],
            ),
        }
    )
