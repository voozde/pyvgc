"""Move models, regulation movepools, and move lookups for Pokémon Champions."""

from __future__ import annotations

import csv
from functools import lru_cache
from importlib import resources
from typing import Mapping, NamedTuple, Optional

from .constants import ALWAYS_HIT_VALUE


class Move(NamedTuple):
    """Move attributes, including whether the move targets multiple Pokémon."""

    name: str
    category: str
    accuracy: Optional[int]
    base_power: Optional[int]
    type: str
    pp: int
    is_spread: bool = False

    @classmethod
    def from_row(cls, row: Mapping[str, str]) -> "Move":
        """Create a move from one move-data CSV row."""
        spread_value = row["IsSpread"].strip().casefold()
        if spread_value not in {"true", "false"}:
            raise ValueError(
                f"invalid IsSpread value for {row['MoveName']!r}: "
                f"{row['IsSpread']!r}"
            )
        return cls(
            name=row["MoveName"],
            category=row["Category"],
            accuracy=(
                None
                if row["Accuracy"] == ALWAYS_HIT_VALUE
                else int(row["Accuracy"])
            ),
            base_power=(
                None
                if row["BasePower"] == "n/a"
                else int(row["BasePower"])
            ),
            type=row["Type"],
            pp=int(row["PP"]),
            is_spread=spread_value == "true",
        )


def create_custom_move(
    name: str,
    base_power: Optional[int],
    move_type: str,
    category: str,
    accuracy: Optional[int] = 100,
    pp: int = 10,
    is_spread: bool = False,
) -> Move:
    """Create a custom move, optionally marking it as a spread-target move."""
    if not isinstance(category, str):
        raise ValueError(
            "move category must be 'Physical', 'Special', or 'Status'"
        )
    normalized_category = category.strip().casefold()
    if normalized_category not in ("physical", "special", "status"):
        raise ValueError(
            "move category must be 'Physical', 'Special', or 'Status'"
        )
    if normalized_category == "status" and base_power is not None:
        raise ValueError("Status moves cannot have base power")
    return Move(
        name=name,
        category=normalized_category.title(),
        accuracy=accuracy,
        base_power=base_power,
        type=move_type,
        pp=pp,
        is_spread=is_spread,
    )


@lru_cache(maxsize=1)
def _move_index() -> dict[str, Move]:
    """Load and cache moves indexed by case-insensitive name."""
    path = resources.files("pyvgc.data").joinpath("move_templates.csv")
    with path.open(newline="", encoding="utf-8") as file:
        return {
            row["MoveName"].casefold(): Move.from_row(row)
            for row in csv.DictReader(file)
        }


def get_move(name: str) -> Move:
    """Return one move by case-insensitive English name."""
    if not isinstance(name, str) or not name.strip():
        raise ValueError("move name must be a non-empty string")
    try:
        return _move_index()[name.strip().casefold()]
    except KeyError:
        raise KeyError(f"Move not found in Pokémon Champions data: {name!r}") from None
