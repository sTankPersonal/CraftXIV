import requests

from app.datasources.base import ItemDataSource
from app.datasources.ingredient_ref import IngredientRef
from app.datasources.parsed_acquisition import ParsedAcquisition
from app.datasources.parsed_item import ParsedItem
from app.datasources.search_result import SearchResult
from app.models.acquisition_type import AcquisitionType


class GarlandToolsDataSource(ItemDataSource):
    """ItemDataSource backed by the public Garland Tools API.

    Item detail responses are shaped like:
        {"item": {"id", "name", "icon", "ilvl", "category", "price",
                   "vendors": [npc ids] (if purchasable), "nodes": [node ids] (if gatherable),
                   "craft": [{"ingredients": [{"id", "amount"}], ...}, ...] (if craftable)},
         "partials": [{"type": "npc", "id", "obj": {"n": name, "a": zone id, "c": [x, y]}}, ...]}

    An item can have any combination of `craft`/`nodes`/`vendors`; each vendor NPC and each
    gathering node becomes its own ParsedAcquisition row (vendor NPC details come from the
    item response's own `partials`; gathering node details require a separate lookup, since
    the item response only gives raw node ids).
    """

    def __init__(
        self,
        base_url: str,
        search_path: str,
        item_path_template: str,
        node_path_template: str,
        session: requests.Session | None = None,
        request_timeout: int = 10,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._search_path = search_path
        self._item_path_template = item_path_template
        self._node_path_template = node_path_template
        self._session = session or requests.Session()
        self._request_timeout = request_timeout

    @classmethod
    def from_app_config(cls, config) -> "GarlandToolsDataSource":
        return cls(
            base_url=config["GARLAND_TOOLS_BASE_URL"],
            search_path=config["GARLAND_TOOLS_SEARCH_PATH"],
            item_path_template=config["GARLAND_TOOLS_ITEM_PATH_TEMPLATE"],
            node_path_template=config["GARLAND_TOOLS_NODE_PATH_TEMPLATE"],
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

        ingredients = []
        if item.get("craft"):
            ingredients = [
                IngredientRef(game_id=ingredient["id"], amount=ingredient["amount"])
                for ingredient in item["craft"][0]["ingredients"]
            ]

        acquisitions = [self._fetch_gather_acquisition(node_id) for node_id in item.get("nodes", [])]

        if item.get("vendors"):
            npc_partials = {
                int(partial["id"]): partial["obj"]
                for partial in payload.get("partials", [])
                if partial["type"] == "npc"
            }
            price = item.get("price")
            acquisitions.extend(
                self._parse_vendor_acquisition(npc_id, npc_partials, price)
                for npc_id in item["vendors"]
            )

        return ParsedItem(
            game_id=item["id"],
            name=item["name"],
            icon_id=item.get("icon"),
            ilvl=item.get("ilvl"),
            category=item.get("category"),
            ingredients=ingredients,
            acquisitions=acquisitions,
            raw_payload=payload,
        )

    def _fetch_gather_acquisition(self, node_id: int) -> ParsedAcquisition:
        url = self._base_url + self._node_path_template.format(node_id=node_id)
        response = self._session.get(url, timeout=self._request_timeout)
        response.raise_for_status()
        node = response.json()["node"]
        coords_x, coords_y = node.get("coords") or (None, None)
        return ParsedAcquisition(
            acquisition_type=AcquisitionType.GATHER,
            location_name=node.get("name"),
            zone_id=node.get("zoneid"),
            coords_x=coords_x,
            coords_y=coords_y,
            node_id=node_id,
            gathering_type=node.get("type"),
            stars=node.get("stars"),
            limit_type=node.get("limitType"),
            time_windows=node.get("time"),
            uptime_minutes=node.get("uptime"),
        )

    @staticmethod
    def _parse_vendor_acquisition(
        npc_id: int, npc_partials: dict[int, dict], price: int | None
    ) -> ParsedAcquisition:
        npc = npc_partials.get(npc_id, {})
        raw_x, raw_y = npc.get("c") or (None, None)
        return ParsedAcquisition(
            acquisition_type=AcquisitionType.VENDOR,
            location_name=npc.get("n"),
            zone_id=npc.get("a"),
            coords_x=float(raw_x) if raw_x is not None else None,
            coords_y=float(raw_y) if raw_y is not None else None,
            npc_id=npc_id,
            price=price,
        )
