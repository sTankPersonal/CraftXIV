import requests

from app.datasources.base import ItemDataSource
from app.datasources.ingredient_ref import IngredientRef
from app.datasources.parsed_acquisition import ParsedAcquisition
from app.datasources.parsed_item import ParsedItem
from app.datasources.search_result import SearchResult
from app.models.acquisition_type import AcquisitionType

# Zone/place names (Garland's `locationIndex`) are a ~2,200-entry static reference table, not
# per-item data - fetched once per process and shared across every GarlandToolsDataSource
# instance (a fresh one is built per request) rather than refetched on every item lookup.
_zone_name_cache: dict[tuple[str, str], dict[int, str]] = {}

# Per-NPC docs (name/zoneid/coords) are likewise static reference data shared across items - an
# NPC selling one item is often referenced by dozens of others, so this is cached across
# requests rather than refetched every time an item mentions the same NPC.
_npc_cache: dict[tuple[str, int], dict] = {}


class GarlandToolsDataSource(ItemDataSource):
    """ItemDataSource backed by the public Garland Tools API.

    Item detail responses are shaped like:
        {"item": {"id", "name", "icon", "ilvl", "category", "price",
                   "craft": [{"ingredients": [{"id", "amount"}], ...}] (if craftable),
                   "nodes": [node ids] (if gatherable),
                   "vendors": [npc ids] (if buyable for gil),
                   "tradeShops": [{"shop", "npcs": [npc ids],
                                    "listings": [{"item": [{"id","amount"}], "currency": [{"id","amount"}]}]}]
                       (if buyable for a special currency),
                   "desynthedFrom": [item ids] (if obtainable by desynthesizing those items),
                   "drops": [mob ids] (if dropped by mobs),
                   "treasure": [treasure map item ids],
                   "leves": [leve ids] (if rewarded from levequests),
                   "ventures": [venture ids] (if rewarded from retainer ventures),
                   "voyages": [{"id", "type"}] (if rewarded from submarine/airship voyages),
                   "supply": {"count", "xp", "seals"} (if a Grand Company supply/provisioning
                       turn-in reward)},
         "partials": [{"type": "npc"|"item"|"mob"|"leve"|..., "id", "obj": {...}}, ...]}

    An item can have any combination of these. Mobs, desynth sources, and treasure maps get
    their display name from this response's own `partials`. Gathering nodes and NPCs need a
    separate per-id lookup: the item response's embedded NPC partial only carries an `areaid`
    (a specific sub-location, e.g. "Loth ast Vath") rather than the NPC's real `zoneid` (e.g.
    "The Dravanian Forelands"), so resolving the actual map name means fetching the NPC's own
    doc rather than trusting the partial.
    """

    def __init__(
        self,
        base_url: str,
        search_path: str,
        item_path_template: str,
        node_path_template: str,
        npc_path_template: str,
        core_data_path: str,
        session: requests.Session | None = None,
        request_timeout: int = 10,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._search_path = search_path
        self._item_path_template = item_path_template
        self._node_path_template = node_path_template
        self._npc_path_template = npc_path_template
        self._core_data_path = core_data_path
        self._session = session or requests.Session()
        self._request_timeout = request_timeout

    @classmethod
    def from_app_config(cls, config) -> "GarlandToolsDataSource":
        return cls(
            base_url=config["GARLAND_TOOLS_BASE_URL"],
            search_path=config["GARLAND_TOOLS_SEARCH_PATH"],
            item_path_template=config["GARLAND_TOOLS_ITEM_PATH_TEMPLATE"],
            node_path_template=config["GARLAND_TOOLS_NODE_PATH_TEMPLATE"],
            npc_path_template=config["GARLAND_TOOLS_NPC_PATH_TEMPLATE"],
            core_data_path=config["GARLAND_TOOLS_CORE_DATA_PATH"],
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
        partials = self._index_partials(payload.get("partials", []))
        # The subject item never appears in its own `partials` (only items it *references* do),
        # so trade shop listings that pay out this same item would otherwise resolve to no name.
        partials.setdefault("item", {})[item["id"]] = {"n": item["name"]}

        ingredients = []
        if item.get("craft"):
            ingredients = [
                IngredientRef(game_id=ingredient["id"], amount=ingredient["amount"])
                for ingredient in item["craft"][0]["ingredients"]
            ]

        acquisitions: list[ParsedAcquisition] = []
        acquisitions += [self._parse_gather(node_id) for node_id in item.get("nodes", [])]
        acquisitions += [
            self._parse_vendor(npc_id, item.get("price")) for npc_id in item.get("vendors", [])
        ]
        acquisitions += self._parse_trade_shops(item.get("tradeShops", []), partials)
        acquisitions += [
            self._parse_named_ref(AcquisitionType.DESYNTH, source_id, partials)
            for source_id in item.get("desynthedFrom", [])
        ]
        acquisitions += [self._parse_drop(mob_id, partials) for mob_id in item.get("drops", [])]
        acquisitions += [
            self._parse_named_ref(AcquisitionType.TREASURE, map_id, partials)
            for map_id in item.get("treasure", [])
        ]
        acquisitions += [self._parse_leve(leve_id, partials) for leve_id in item.get("leves", [])]
        acquisitions += [
            ParsedAcquisition(acquisition_type=AcquisitionType.VENTURE, ref_id=venture_id)
            for venture_id in item.get("ventures", [])
        ]
        acquisitions += [self._parse_voyage(voyage) for voyage in item.get("voyages", [])]
        if item.get("supply"):
            acquisitions.append(self._parse_supply(item["supply"]))

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

    @staticmethod
    def _index_partials(partials: list[dict]) -> dict[str, dict[int, dict]]:
        """Group the response's flat `partials` list by type, e.g. index["npc"][1005633].

        A few partials use synthetic non-numeric ids instead of a real game id - e.g. FC
        workshop (submersible/airship) recipes reference a blueprint via `unlockId: "draft26"`,
        which shows up here as an `item` partial with id "draft26". We never look those up
        (nothing we parse points at a blueprint id), so they're skipped rather than crashing.
        """
        index: dict[str, dict[int, dict]] = {}
        for partial in partials:
            try:
                ref_id = int(partial["id"])
            except (TypeError, ValueError):
                continue
            index.setdefault(partial["type"], {})[ref_id] = partial["obj"]
        return index

    def _fetch_npc(self, npc_id: int) -> dict:
        cache_key = (self._base_url, npc_id)
        npc = _npc_cache.get(cache_key)
        if npc is None:
            url = self._base_url + self._npc_path_template.format(npc_id=npc_id)
            response = self._session.get(url, timeout=self._request_timeout)
            response.raise_for_status()
            npc = response.json()["npc"]
            _npc_cache[cache_key] = npc
        return npc

    @staticmethod
    def _npc_location(npc: dict) -> tuple[str | None, int | None, float | None, float | None]:
        raw_x, raw_y = npc.get("coords") or (None, None)
        return (
            npc.get("name"),
            npc.get("zoneid"),
            float(raw_x) if raw_x is not None else None,
            float(raw_y) if raw_y is not None else None,
        )

    def _zone_name(self, zone_id: int | None) -> str | None:
        """Resolve a zone/place id to its display name (e.g. 45 -> "Southern Thanalan") via
        Garland's core `locationIndex`, a static reference table fetched once per process."""
        if zone_id is None:
            return None
        cache_key = (self._base_url, self._core_data_path)
        zone_names = _zone_name_cache.get(cache_key)
        if zone_names is None:
            url = self._base_url + self._core_data_path
            response = self._session.get(url, timeout=self._request_timeout)
            response.raise_for_status()
            zone_names = {
                int(location_id): location["name"]
                for location_id, location in response.json().get("locationIndex", {}).items()
            }
            _zone_name_cache[cache_key] = zone_names
        return zone_names.get(zone_id)

    def _parse_gather(self, node_id: int) -> ParsedAcquisition:
        url = self._base_url + self._node_path_template.format(node_id=node_id)
        response = self._session.get(url, timeout=self._request_timeout)
        response.raise_for_status()
        node = response.json()["node"]
        coords_x, coords_y = node.get("coords") or (None, None)
        zone_id = node.get("zoneid")
        return ParsedAcquisition(
            acquisition_type=AcquisitionType.GATHER,
            location_name=node.get("name"),
            zone_id=zone_id,
            zone_name=self._zone_name(zone_id),
            coords_x=coords_x,
            coords_y=coords_y,
            ref_id=node_id,
            details={
                "gathering_type": node.get("type"),
                "stars": node.get("stars"),
                "limited": bool(node.get("limited")),
                "limit_type": node.get("limitType"),
                "time_windows": node.get("time"),
                "uptime_minutes": node.get("uptime"),
            },
        )

    def _parse_vendor(self, npc_id: int, price: int | None) -> ParsedAcquisition:
        name, zone_id, coords_x, coords_y = self._npc_location(self._fetch_npc(npc_id))
        return ParsedAcquisition(
            acquisition_type=AcquisitionType.VENDOR,
            location_name=name,
            zone_id=zone_id,
            zone_name=self._zone_name(zone_id),
            coords_x=coords_x,
            coords_y=coords_y,
            ref_id=npc_id,
            details={"price": price},
        )

    def _parse_trade_shops(
        self, shops: list[dict], partials: dict[str, dict[int, dict]]
    ) -> list[ParsedAcquisition]:
        items_by_id = partials.get("item", {})
        acquisitions = []
        for shop in shops:
            listings = [
                {
                    "receive": self._describe_listing(listing.get("item", []), items_by_id),
                    "cost": self._describe_listing(listing.get("currency", []), items_by_id),
                }
                for listing in shop.get("listings", [])
            ]
            details = {"shop_name": shop.get("shop"), "listings": listings}
            npc_ids = shop.get("npcs") or []
            if not npc_ids:
                # A few shops (e.g. "Materia I") list no npcs at all - keep the shop name as the
                # only location info rather than skipping the acquisition entirely.
                acquisitions.append(
                    ParsedAcquisition(
                        acquisition_type=AcquisitionType.TRADE_SHOP,
                        location_name=shop.get("shop"),
                        details=details,
                    )
                )
                continue
            for npc_id in npc_ids:
                name, zone_id, coords_x, coords_y = self._npc_location(self._fetch_npc(npc_id))
                acquisitions.append(
                    ParsedAcquisition(
                        acquisition_type=AcquisitionType.TRADE_SHOP,
                        location_name=name or shop.get("shop"),
                        zone_id=zone_id,
                        zone_name=self._zone_name(zone_id),
                        coords_x=coords_x,
                        coords_y=coords_y,
                        ref_id=npc_id,
                        details=details,
                    )
                )
        return acquisitions

    @staticmethod
    def _describe_listing(entries: list[dict], items_by_id: dict[int, dict]) -> list[dict]:
        return [
            {
                "id": int(entry["id"]),
                "amount": entry["amount"],
                "name": items_by_id.get(int(entry["id"]), {}).get("n"),
            }
            for entry in entries
        ]

    @staticmethod
    def _parse_named_ref(
        acquisition_type: AcquisitionType, ref_id: int, partials: dict[str, dict[int, dict]]
    ) -> ParsedAcquisition:
        """Build a bare acquisition for types that are just an id list in the item payload
        (desynth sources, treasure maps) and whose display name comes from an `item` partial."""
        source = partials.get("item", {}).get(int(ref_id), {})
        return ParsedAcquisition(
            acquisition_type=acquisition_type,
            location_name=source.get("n"),
            ref_id=int(ref_id),
        )

    def _parse_drop(self, mob_id: int, partials: dict[str, dict[int, dict]]) -> ParsedAcquisition:
        mob = partials.get("mob", {}).get(int(mob_id), {})
        zone_id = mob.get("z")
        return ParsedAcquisition(
            acquisition_type=AcquisitionType.DROP,
            location_name=mob.get("n"),
            zone_id=zone_id,
            zone_name=self._zone_name(zone_id),
            ref_id=int(mob_id),
            details={"level": mob["l"]} if mob.get("l") is not None else {},
        )

    @staticmethod
    def _parse_leve(leve_id: int, partials: dict[str, dict[int, dict]]) -> ParsedAcquisition:
        leve = partials.get("leve", {}).get(int(leve_id), {})
        return ParsedAcquisition(
            acquisition_type=AcquisitionType.LEVE,
            location_name=leve.get("n"),
            ref_id=int(leve_id),
            details={"level": leve["l"]} if leve.get("l") is not None else {},
        )

    @staticmethod
    def _parse_voyage(voyage: dict) -> ParsedAcquisition:
        return ParsedAcquisition(
            acquisition_type=AcquisitionType.VOYAGE,
            ref_id=voyage.get("id"),
            details={"voyage_type": voyage.get("type")},
        )

    @staticmethod
    def _parse_supply(supply: dict) -> ParsedAcquisition:
        return ParsedAcquisition(
            acquisition_type=AcquisitionType.SUPPLY,
            details={
                "count": supply.get("count"),
                "xp": supply.get("xp"),
                "seals": supply.get("seals"),
            },
        )
