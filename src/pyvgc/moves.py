"""Cached move and learnset lookups for Pokémon Champions."""

from __future__ import annotations

import csv
from functools import lru_cache
from importlib import resources
from typing import Mapping, NamedTuple, Optional

from .constants import ALWAYS_HIT_VALUE


class Move(NamedTuple):
    """The currently implemented, effect-independent move attributes."""

    name: str
    category: str
    accuracy: Optional[int]
    base_power: Optional[int]
    type: str
    pp: int

    @classmethod
    def from_row(cls, row: Mapping[str, str]) -> "Move":
        """Create a move from one move-data CSV row."""
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
