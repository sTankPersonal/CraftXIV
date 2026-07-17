from enum import Enum


class AcquisitionType(str, Enum):
    """How an item is obtained. Determines whether it is a leaf in the crafting tree."""

    CRAFT = "craft"
    GATHER = "gather"
    VENDOR = "vendor"
    TRADE_SHOP = "trade_shop"
    DESYNTH = "desynth"
    DROP = "drop"
    TREASURE = "treasure"
    LEVE = "leve"
    VENTURE = "venture"
    VOYAGE = "voyage"
    SUPPLY = "supply"
    UNKNOWN = "unknown"
