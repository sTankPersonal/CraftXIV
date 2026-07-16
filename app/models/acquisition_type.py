from enum import Enum


class AcquisitionType(str, Enum):
    """How an item is obtained. Determines whether it is a leaf in the crafting tree."""

    CRAFT = "craft"
    GATHER = "gather"
    VENDOR = "vendor"
    UNKNOWN = "unknown"
