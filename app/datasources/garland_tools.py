import requests

from app.datasources.base import ItemDataSource
from app.datasources.ingredient_ref import IngredientRef
from app.datasources.parsed_item import ParsedItem
from app.datasources.search_result import SearchResult
from app.models.acquisition_type import AcquisitionType


class GarlandToolsDataSource(ItemDataSource):
    """ItemDataSource backed by the public Garland Tools API.

    Item detail responses are shaped like:
        {"item": {"id", "name", "icon", "ilvl", "category", "price",
                   "vendors": [...] (if purchasable), "nodes": [...] (if gatherable),
                   "craft": [{"ingredients": [{"id", "amount"}], ...}, ...] (if craftable)}}
    Acquisition type is derived from which of `craft`/`nodes`/`vendors` is present, in that
    priority order, falling back to UNKNOWN for quest/drop-only items.
    """

    def __init__(
        self,
        base_url: str,
        search_path: str,
        item_path_template: str,
        session: requests.Session | None = None,
        request_timeout: int = 10,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._search_path = search_path
        self._item_path_template = item_path_template
        self._session = session or requests.Session()
        self._request_timeout = request_timeout

    @classmethod
    def from_app_config(cls, config) -> "GarlandToolsDataSource":
        return cls(
            base_url=config["GARLAND_TOOLS_BASE_URL"],
            search_path=config["GARLAND_TOOLS_SEARCH_PATH"],
            item_path_template=config["GARLAND_TOOLS_ITEM_PATH_TEMPLATE"],
            request_timeout=config["GARLAND_TOOLS_REQUEST_TIMEOUT"],
        )

    def fetch_item(self, game_id: int) -> ParsedItem:
        url = self._base_url + self._item_path_template.format(game_id=game_id)
        response = self._session.get(url, timeout=self._request_timeout)
        response.raise_for_status()
        return self._parse_item(response.json())

    def search(self, text: str) -> list[SearchResult]:
        url = self._base_url + self._search_path
        response = self._session.get(
            url, params={"text": text, "type": "item"}, timeout=self._request_timeout
        )
        response.raise_for_status()
        return [
            SearchResult(game_id=hit["obj"]["i"], name=hit["obj"]["n"])
            for hit in response.json()
        ]

    def _parse_item(self, payload: dict) -> ParsedItem:
        item = payload["item"]

        acquisition_type = self._determine_acquisition_type(item)
        ingredients = []
        vendor_price = None
        gathering_node_ids = None

        if acquisition_type == AcquisitionType.CRAFT:
            ingredients = [
                IngredientRef(game_id=ingredient["id"], amount=ingredient["amount"])
                for ingredient in item["craft"][0]["ingredients"]
            ]
        elif acquisition_type == AcquisitionType.GATHER:
            gathering_node_ids = list(item["nodes"])
        elif acquisition_type == AcquisitionType.VENDOR:
            vendor_price = item.get("price")

        return ParsedItem(
            game_id=item["id"],
            name=item["name"],
            icon_id=item.get("icon"),
            ilvl=item.get("ilvl"),
            category=item.get("category"),
            acquisition_type=acquisition_type,
            vendor_price=vendor_price,
            gathering_node_ids=gathering_node_ids,
            ingredients=ingredients,
            raw_payload=payload,
        )

    @staticmethod
    def _determine_acquisition_type(item: dict) -> AcquisitionType:
        if item.get("craft"):
            return AcquisitionType.CRAFT
        if item.get("nodes"):
            return AcquisitionType.GATHER
        if item.get("vendors"):
            return AcquisitionType.VENDOR
        return AcquisitionType.UNKNOWN
