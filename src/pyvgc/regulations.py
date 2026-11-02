"""Load bundled regulation snapshots for data queries."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field, replace
from functools import lru_cache
from importlib import resources
from types import MappingProxyType
from typing import Any, Mapping, Optional, Union

from .battle_logic import BattleLogic, get_battle_logic
from .items import Item
from .moves import Move
from .pokemon import Pokemon

MECHANICS = ("MegaEvolution", "ZMoves", "Dynamax", "Teratype")
REGULATION_ORDER = ("M-A", "M-B", "M-C")
PLATFORM_ORDER = ("Cartridge", "Simulator")
_MISSING_DATA_VALUE = "n/a"
_METADATA_FILE = resources.files("pyvgc.data").joinpath(
    "list_of_regulations.csv"
)


@dataclass(frozen=True)
class RegulationItem:
    """An item available in a regulation snapshot."""

    name: str
    regulation: str
    released_in_regulation: str
    description: str


@dataclass(frozen=True)
class RegulationData:
    """Immutable data loaded from one regulation snapshot."""

    name: str
    platform: str
    battle_logic: BattleLogic
    mechanics: Mapping[str, bool]
    pokemon: tuple[Mapping[str, str], ...]
    items: tuple[str, ...]
    moves: tuple[Move, ...]
    learnsets: Mapping[str, tuple[Move, ...]]
    abilities: Mapping[str, tuple[str, ...]]
    item_data: Mapping[str, RegulationItem]
    _pokemon_index: Mapping[str, Mapping[str, str]] = field(
        default_factory=lambda: MappingProxyType({}),
        repr=False,
        compare=False,
    )
    _move_index: Mapping[str, Move] = field(
        default_factory=lambda: MappingProxyType({}),
        repr=False,
        compare=False,
    )
    _learnsets_by_pokemon: Mapping[str, tuple[Move, ...]] = field(
        default_factory=lambda: MappingProxyType({}),
        repr=False,
        compare=False,
    )
    _pokemon_by_move: Mapping[str, tuple[str, ...]] = field(
        default_factory=lambda: MappingProxyType({}),
        repr=False,
        compare=False,
    )
    _signature_move_index: tuple[tuple[str, str], ...] = field(
        default=(),
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        """Build immutable lookup indexes once for this regulation snapshot."""
        if (
            self._pokemon_index
            and self._move_index
            and self._learnsets_by_pokemon
            and self._pokemon_by_move
        ):
            return

        pokemon_index: dict[str, Mapping[str, str]] = {}
        for pokemon in self.pokemon:
            pokemon_index.setdefault(pokemon["PokemonName"].casefold(), pokemon)

        move_index: dict[str, Move] = {}
        for move in self.moves:
            move_index.setdefault(move.name.casefold(), move)

        learnsets_by_pokemon = {
            pokemon_name.casefold(): moves
            for pokemon_name, moves in self.learnsets.items()
        }
        users_by_move: dict[str, dict[str, list[str]]] = {}
        for pokemon_name, moves in self.learnsets.items():
            species_number = pokemon_index[pokemon_name.casefold()][
                "PokemonNumber"
            ]
            for move in moves:
                users_by_move.setdefault(
                    move.name.casefold(), {}
                ).setdefault(species_number, []).append(pokemon_name)

        pokemon_by_move = {}
        for move_key, species_users in users_by_move.items():
            users = [
                pokemon_name
                for pokemon_names in species_users.values()
                for pokemon_name in pokemon_names
            ]
            pokemon_by_move[move_key] = tuple(
                sorted(users, key=str.casefold)
            )

        signature_moves = []
        for move_key, species_users in users_by_move.items():
            if len(species_users) == 1:
                signature_moves.extend(
                    (move_index[move_key].name, pokemon_name)
                    for pokemon_names in species_users.values()
                    for pokemon_name in pokemon_names
                )

        object.__setattr__(
            self, "_pokemon_index", MappingProxyType(pokemon_index)
        )
        object.__setattr__(self, "_move_index", MappingProxyType(move_index))
        object.__setattr__(
            self,
            "_learnsets_by_pokemon",
            MappingProxyType(learnsets_by_pokemon),
        )
        object.__setattr__(
            self, "_pokemon_by_move", MappingProxyType(pokemon_by_move)
        )
        object.__setattr__(
            self,
            "_signature_move_index",
            tuple(sorted(
                signature_moves,
                key=lambda pair: (pair[0].casefold(), pair[1].casefold()),
            )),
        )

    def __repr__(self) -> str:
        """Return a concise representation of the loaded regulation."""
        return (
            f"RegulationData(name={self.name!r}, platform={self.platform!r}, "
            f"pokemon={len(self.pokemon)}, items={len(self.items)}, "
            f"moves={len(self.moves)})"
        )

    __str__ = __repr__

    def mechanic_available(self, mechanic: str) -> bool:
        """Return whether a named mechanic is enabled."""
        if not isinstance(mechanic, str):
            raise ValueError("mechanic must be a string")
        try:
            return self.mechanics[mechanic.strip()]
        except KeyError:
            supported = ", ".join(MECHANICS)
            raise ValueError(
                f"Unknown mechanic {mechanic!r}; supported mechanics: {supported}"
            ) from None

    @property
    def pokemon_names(self) -> tuple[str, ...]:
        """Return Pokémon form names in the snapshot."""
        return tuple(row["PokemonName"] for row in self.pokemon)

    @property
    def move_names(self) -> tuple[str, ...]:
        """Return available move names in the snapshot."""
        return tuple(move.name for move in self.moves)

    @property
    def ability_names(self) -> tuple[str, ...]:
        """Return unique ability names in case-insensitive order."""
        return tuple(sorted(
            {
                ability
                for abilities in self.abilities.values()
                for ability in abilities
            },
            key=str.casefold,
        ))

    def item(self, name: str) -> RegulationItem:
        """Return one item by case-insensitive name."""
        if not isinstance(name, str) or not name.strip():
            raise ValueError("item name must be a non-empty string")
        try:
            return self.item_data[name.strip().casefold()]
        except KeyError:
            raise KeyError(
                f"Item {name!r} is unavailable in regulation {self.name}"
            ) from None

    def get_item(self, name: str) -> Item:
        """Return a legal immutable item model."""
        item = self.item(name)
        return Item(item.name, item.description)

    def get_move(self, name: str) -> Move:
        """Return a legal move."""
        return self.move(name)

    def load_pokemon(
        self,
        name: str,
        stat_training: Optional[Mapping[str, int]] = None,
        nature: Optional[str] = None,
        stat_stages: Optional[Mapping[str, int]] = None,
        item: Optional[Union[str, Item]] = None,
    ) -> Pokemon:
        """Load a legal Pokémon with optional regulation-valid item."""
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Pokémon name must be a non-empty string")
        key = name.strip().casefold()
        try:
            row = self._pokemon_index[key]
        except KeyError:
            raise KeyError(
                f"Pokémon {name!r} is unavailable in regulation {self.name}"
            ) from None
        legal_item = None if item is None else self.get_item(
            item.name if isinstance(item, Item) else item
        )
        return Pokemon(
            int(row["PokemonNumber"]), row["PokemonName"],
            int(row["PokemonHP"]), int(row["PokemonAtk"]),
            int(row["PokemonDef"]), int(row["PokemonSPAtk"]),
            int(row["PokemonSPDef"]), int(row["PokemonSpeed"]),
            tuple(value for value in (row["Type1"], row["Type2"]) if value != "n/a"),
            stat_training=stat_training,
            nature=nature,
            stat_stages=stat_stages,
            logic=self.battle_logic,
            item=legal_item,
            regulation=self.name,
        )

    def get_moves_for_pokemon(self, name: str) -> tuple[Move, ...]:
        """Return the legal learnset for one Pokémon."""
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Pokémon name must be a non-empty string")
        key = name.strip().casefold()
        try:
            return self._learnsets_by_pokemon[key]
        except KeyError:
            raise KeyError(
                f"Pokémon {name!r} is unavailable in regulation {self.name}"
            ) from None

    def move(self, name: str) -> Move:
        """Return one available move by case-insensitive name."""
        if not isinstance(name, str) or not name.strip():
            raise ValueError("move name must be a non-empty string")
        key = name.strip().casefold()
        try:
            return self._move_index[key]
        except KeyError:
            raise KeyError(
                f"Move {name!r} is unavailable in regulation {self.name}"
            ) from None


def _read_csv(path: Any) -> list[dict[str, str]]:
    """Read a UTF-8 CSV resource."""
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _normalize_regulation(regulation: str) -> str:
    """Return a canonical regulation name."""
    if not isinstance(regulation, str):
        raise ValueError("regulation must be a string")
    value = regulation.strip().upper()
    if value not in REGULATION_ORDER:
        supported = ", ".join(REGULATION_ORDER)
        raise ValueError(
            f"Unknown regulation {regulation!r}; supported regulations: {supported}"
        )
    return value


def _snapshot_path(regulation: str, filename: str) -> Any:
    """Return a path inside one bundled regulation snapshot."""
    return resources.files("pyvgc.data").joinpath(
        "regulations", regulation.casefold().replace("-", "_"), filename
    )


def _normalize_platform(platform: str) -> str:
    """Return a canonical platform name."""
    if not isinstance(platform, str):
        raise ValueError("platform must be a string")
    value = platform.strip().title()
    if value not in PLATFORM_ORDER:
        supported = ", ".join(PLATFORM_ORDER)
        raise ValueError(
            f"Unknown platform {platform!r}; supported platforms: {supported}"
        )
    return value


@lru_cache(maxsize=1)
def _metadata() -> Mapping[
    str, Mapping[str, tuple[BattleLogic, Mapping[str, bool]]]
]:
    """Load and validate regulation metadata."""
    metadata = {}
    for row in _read_csv(_METADATA_FILE):
        name = row["Regulation"].strip().upper()
        if name in metadata:
            raise ValueError(f"Duplicate metadata for regulation {name!r}")
        mechanics = MappingProxyType({
            mechanic: row.get(mechanic, "no").strip().casefold() == "yes"
            for mechanic in MECHANICS
        })
        platform_metadata = {}
        for platform in PLATFORM_ORDER:
            logic_name = row.get(platform, "").strip()
            if not logic_name:
                raise ValueError(
                    f"Missing {platform} battle logic for regulation {name!r}"
                )
            platform_metadata[platform] = (
                get_battle_logic(logic_name),
                mechanics,
            )
        metadata[name] = MappingProxyType(platform_metadata)
    return MappingProxyType(metadata)


@lru_cache(maxsize=None)
def _load_regulation(name: str, platform: str) -> RegulationData:
    """Load and cache one canonical regulation snapshot."""
    try:
        logic, mechanics = _metadata()[name][platform]
    except KeyError:
        raise ValueError(
            f"Missing metadata for regulation {name!r} and platform {platform!r}"
        ) from None

    roster = tuple(
        MappingProxyType(row)
        for row in _read_csv(_snapshot_path(name, "pokemon.csv"))
    )
    item_rows = _read_csv(_snapshot_path(name, "items.csv"))
    move_rows = _read_csv(_snapshot_path(name, "moves.csv"))
    move_index = {
        row["MoveName"].casefold(): Move.from_row(row)
        for row in move_rows
    }

    learnsets = {}
    for row in _read_csv(_snapshot_path(name, "learnsets.csv")):
        names = tuple(
            move for move in row["Moves"].split(";")
            if move != _MISSING_DATA_VALUE
        )
        if names:
            learnsets[row["PokemonName"]] = tuple(
                move_index[move.casefold()] for move in names
            )

    abilities = {
        row["PokemonName"]: tuple(
            value for key in ("Ability1", "Ability2", "Ability3")
            if (value := row.get(key, _MISSING_DATA_VALUE))
            != _MISSING_DATA_VALUE
        )
        for row in roster
    }

    return RegulationData(
        name=name,
        platform=platform,
        battle_logic=logic,
        mechanics=mechanics,
        pokemon=roster,
        items=tuple(row["ItemName"] for row in item_rows),
        moves=tuple(sorted(move_index.values(), key=lambda move: move.name.casefold())),
        learnsets=MappingProxyType(learnsets),
        abilities=MappingProxyType(abilities),
        item_data=MappingProxyType({
            row["ItemName"].casefold(): RegulationItem(
                row["ItemName"],
                name,
                row["ReleasedInRegulation"].strip().upper(),
                row["Description"],
            )
            for row in item_rows
        }),
    )


def load_regulation(
    regulation: str,
    platform: str = "Cartridge",
    battle_logic: Optional[Union[str, BattleLogic]] = None,
) -> RegulationData:
    """Return a regulation snapshot with the selected battle logic.

    The platform selects the battle logic from the regulation metadata by
    default. ``battle_logic`` can override that selection with a registered
    logic name or an explicit ``BattleLogic`` instance.
    """
    normalized_platform = _normalize_platform(platform)
    snapshot = _load_regulation(
        _normalize_regulation(regulation),
        normalized_platform,
    )
    if battle_logic is None:
        return snapshot
    if isinstance(battle_logic, str):
        selected_logic = get_battle_logic(battle_logic)
    elif isinstance(battle_logic, BattleLogic):
        selected_logic = battle_logic
    else:
        raise TypeError("battle_logic must be a name or BattleLogic instance")
    return replace(snapshot, battle_logic=selected_logic)
