"""Immutable item data models and bundled item lookup."""

import csv
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources


@dataclass(frozen=True)
class Item:
    """A held item and its descriptive effect."""

    name: str
    description: str = ""


@lru_cache(maxsize=1)
def _item_index() -> dict[str, Item]:
    """Load the canonical packaged item catalog."""
    path = resources.files("pyvgc.data").joinpath("battle_items.csv")
    with path.open(newline="", encoding="utf-8") as file:
        return {
            row["ItemName"].casefold(): Item(row["ItemName"], row["Description"])
            for row in csv.DictReader(file)
        }


def get_item(name: str) -> Item:
    """Return one canonical item by case-insensitive name."""
    if not isinstance(name, str) or not name.strip():
        raise ValueError("item name must be a non-empty string")
    try:
        return _item_index()[name.strip().casefold()]
    except KeyError:
        raise KeyError(f"Unknown item: {name!r}") from None
