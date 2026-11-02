"""Level-50 Pokémon models loaded from the packaged roster."""

from __future__ import annotations

import csv
from functools import lru_cache
from importlib import resources
from types import MappingProxyType
from typing import Iterable, Mapping, NamedTuple, Optional, Union

from .battle_logic import BattleLogic, CARTRIDGE_CHAMPIONS_RELEASE_2026
from .constants import NATURES, STAT_NAMES, TYPES
from .items import Item, get_item
from .moves import Move
from .utils import get_moves_for_pokemon


class RosterEntry(NamedTuple):
    """Immutable base-stat record loaded from the Pokémon roster."""

    number: int
    name: str
    hp: int
    attack: int
    defense: int
    special_attack: int
    special_defense: int
    speed: int
    types: tuple[str, ...]


class Pokemon:
    """A level-50 Pokémon loaded from the roster."""

    __slots__ = (
        "number", "name", "hp", "attack", "defense", "special_attack",
        "special_defense", "speed", "_types", "_item", "nature",
        "_pre_stage_stats", "_stat_stages",
        "_logic",
    )

    def __init__(
        self,
        number: int,
        name: str,
        hp: int,
        attack: int,
        defense: int,
        special_attack: int,
        special_defense: int,
        speed: int,
        types: tuple[str, ...],
        stat_training: Optional[Mapping[str, int]] = None,
        nature: Optional[str] = None,
        stat_stages: Optional[Mapping[str, int]] = None,
        logic: BattleLogic = CARTRIDGE_CHAMPIONS_RELEASE_2026,
        item: Optional[Union[str, Item]] = None,
    ) -> None:
        """Create a Pokémon from base stats and optional battle settings.

        ``item`` may be an item name or canonical ``Item`` instance. Unknown
        item names are rejected in the same way as :meth:`set_item`.
        """
        if not isinstance(logic, BattleLogic):
            raise TypeError("logic must be a BattleLogic instance")
        self._logic = logic
        training = {**dict.fromkeys(STAT_NAMES, 0), **(stat_training or {})}
        if set(training) != set(STAT_NAMES):
            raise ValueError("stat_training contains an unknown stat")
        if any(
            type(value) is not int or not 0 <= value <= logic.max_training_per_stat
            for value in training.values()
        ):
            raise ValueError(
                f"each training value must be an integer from 0 to "
                f"{logic.max_training_per_stat}"
            )
        if sum(training.values()) > logic.max_total_training:
            raise ValueError(
                f"stat training cannot exceed {logic.max_total_training} total points"
            )

        self.number = number
        self.name = name
        self.hp = hp + logic.base_hp_increase + training["hp"]
        self.attack = attack + logic.base_stat_increase + training["attack"]
        self.defense = defense + logic.base_stat_increase + training["defense"]
        self.special_attack = (
            special_attack + logic.base_stat_increase + training["special_attack"]
        )
        self.special_defense = (
            special_defense + logic.base_stat_increase + training["special_defense"]
        )
        self.speed = speed + logic.base_stat_increase + training["speed"]
        self.set_types(types)
        self._item = None
        self.set_item(item)

        normalized_nature = None
        if nature is not None:
            try:
                normalized_nature = nature.strip().title()
                raised, lowered = NATURES[normalized_nature]
            except KeyError:
                raise ValueError(f"unknown nature: {nature!r}") from None
            if raised != lowered:
                setattr(self, raised, getattr(self, raised) * 11 // 10)
                setattr(self, lowered, getattr(self, lowered) * 9 // 10)
        self.nature = normalized_nature
        self._pre_stage_stats = {
            stat: getattr(self, stat) for stat in STAT_NAMES[1:]
        }

        stages = stat_stages or {}
        if "hp" in stages or any(stat not in STAT_NAMES[1:] for stat in stages):
            raise ValueError("stat_stages can only contain non-HP stats")
        if any(
            type(stage) is not int
            or not logic.min_stat_stage <= stage <= logic.max_stat_stage
            for stage in stages.values()
        ):
            raise ValueError(
                f"each stat stage must be an integer from "
                f"{logic.min_stat_stage} to {logic.max_stat_stage}"
            )
        for stat, stage in stages.items():
            numerator, denominator = logic.stat_stage_multipliers[stage]
            setattr(self, stat, getattr(self, stat) * numerator // denominator)
        self._stat_stages = dict(stages)

    @property
    def stat_stages(self) -> Mapping[str, int]:
        """Return configured battle stages without exposing mutable state."""
        return MappingProxyType(self._stat_stages)

    @property
    def types(self) -> tuple[str, ...]:
        """Return the Pokémon's current battle types."""
        return self._types

    @types.setter
    def types(self, types: Iterable[str]) -> None:
        """Set the Pokémon's current battle types."""
        self.set_types(types)

    def get_types(self) -> tuple[str, ...]:
        """Return the Pokémon's current battle types."""
        return self._types

    def info(self) -> dict[str, object]:
        """Return the Pokémon's current stats, types, nature, and item."""
        return {
            "name": self.name,
            "stats": {
                stat: getattr(self, stat)
                for stat in STAT_NAMES
            },
            "types": self.types,
            "nature": self.nature,
            "item": self.get_item(),
        }

    def set_stats(self, stats: Mapping[str, int]) -> None:
        """Set selected current stats to exact values.

        Directly set stats replace the selected battle stats and clear any
        stat stage on those stats so the assigned values remain exact.
        """
        if not isinstance(stats, Mapping) or not stats:
            raise ValueError("stats must be a non-empty mapping")
        unknown = set(stats) - set(STAT_NAMES)
        if unknown:
            raise ValueError(
                f"stats contains unknown stat(s): {', '.join(sorted(unknown))}"
            )
        if any(type(value) is not int or value <= 0 for value in stats.values()):
            raise ValueError("stat values must be positive integers")

        for stat, value in stats.items():
            setattr(self, stat, value)
            if stat != "hp":
                self._pre_stage_stats[stat] = value
                self._stat_stages.pop(stat, None)

    @property
    def battle_logic(self) -> BattleLogic:
        """Return the battle logic used by this Pokémon."""
        return self._logic

    def set_types(self, types: Iterable[str]) -> None:
        """Set one or two valid, distinct Pokémon types.

        Type changes affect subsequent damage calculations and do not alter
        the Pokémon's roster data.
        """
        if isinstance(types, str):
            raise ValueError("types must be an iterable of type names")
        normalized = tuple(self._normalize_type(type_name) for type_name in types)
        if not normalized or len(normalized) > 2:
            raise ValueError("a Pokémon must have one or two types")
        if len(set(normalized)) != len(normalized):
            raise ValueError("a Pokémon cannot have duplicate types")
        self._types = normalized

    def get_item(self) -> Optional[str]:
        """Return the Pokémon's currently held item, if any."""
        return self._item

    def set_item(self, item: Optional[Union[str, Item]]) -> None:
        """Set or remove the Pokémon's held item.

        Item effects are not implemented by the damage calculator; this
        stores the selected item for future battle logic.
        """
        if item is None:
            self._item = None
            return
        item_name = item.name if isinstance(item, Item) else item
        canonical_item = get_item(item_name)
        self._item = canonical_item.name

    @staticmethod
    def _normalize_type(type_name: str) -> str:
        """Validate and canonicalize one Pokémon type name."""
        if not isinstance(type_name, str):
            raise ValueError("type names must be strings")
        normalized = type_name.strip().title()
        if normalized not in TYPES:
            raise ValueError(f"unknown Pokémon type: {type_name!r}")
        return normalized

    @classmethod
    def load(
        cls,
        name: str,
        stat_training: Optional[Mapping[str, int]] = None,
        nature: Optional[str] = None,
        stat_stages: Optional[Mapping[str, int]] = None,
        logic: BattleLogic = CARTRIDGE_CHAMPIONS_RELEASE_2026,
        item: Optional[Union[str, Item]] = None,
    ) -> "Pokemon":
        """Load one canonical roster form with optional battle settings."""
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Pokémon name must be a non-empty string")
        try:
            entry = _roster_index()[name.strip().casefold()]
        except KeyError:
            raise KeyError(f"Pokémon not found in roster: {name!r}") from None
        return cls(
            *entry,
            stat_training=stat_training,
            nature=nature,
            stat_stages=stat_stages,
            logic=logic,
            item=item,
        )

    @property
    def moves(self) -> tuple[Move, ...]:
        """Return this form's available moves in alphabetical order."""
        return get_moves_for_pokemon(self.name)


@lru_cache(maxsize=1)
def _roster() -> tuple[RosterEntry, ...]:
    """Read and cache the packaged roster."""
    path = resources.files("pyvgc.data").joinpath("full_pokemon_roster.csv")
    with path.open(newline="", encoding="utf-8") as file:
        return tuple(
            RosterEntry(
                int(row["PokemonNumber"]),
                row["PokemonName"],
                int(row["PokemonHP"]),
                int(row["PokemonAtk"]),
                int(row["PokemonDef"]),
                int(row["PokemonSPAtk"]),
                int(row["PokemonSPDef"]),
                int(row["PokemonSpeed"]),
                tuple(
                    type_name for type_name in (row["Type1"], row["Type2"])
                    if type_name and type_name != "n/a"
                ),
            )
            for row in csv.DictReader(file)
        )


@lru_cache(maxsize=1)
def _roster_index() -> dict[str, RosterEntry]:
    """Return a case-insensitive canonical-name roster index."""
    return {entry.name.casefold(): entry for entry in _roster()}
