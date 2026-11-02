"""Public API for the pyvgc package."""

from importlib.metadata import PackageNotFoundError, version

from .battle_logic import (
    BattleLogic,
    CARTRIDGE_CHAMPIONS_RELEASE_2026,
    CHAMPIONS_SINGLES,
    SIMULATOR_CHAMPIONS_RELEASE_2026,
    get_battle_logic,
)
from .damage import calculate_damage, damage_rolls
from .items import Item, get_item
from .moves import Move, get_move
from .pokemon import Pokemon
from .regulations import load_regulation
from .utils import (
    get_moves_for_pokemon,
    get_pokemon_for_move,
    pokemon_with_ability,
    pokemon_with_single_ability,
    regulation_description,
    signature_moves,
)

try:
    __version__ = version("pyvgc")
except PackageNotFoundError:
    __version__ = "0.0.2.4"

__all__ = [
    "__version__",
    "BattleLogic",
    "CARTRIDGE_CHAMPIONS_RELEASE_2026",
    "CHAMPIONS_SINGLES",
    "SIMULATOR_CHAMPIONS_RELEASE_2026",
    "Item",
    "Move",
    "Pokemon",
    "calculate_damage",
    "damage_rolls",
    "get_battle_logic",
    "get_item",
    "get_move",
    "get_moves_for_pokemon",
    "get_pokemon_for_move",
    "load_regulation",
    "pokemon_with_ability",
    "pokemon_with_single_ability",
    "regulation_description",
    "signature_moves",
]