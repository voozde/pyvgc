"""Named battle-rule configurations used by regulations."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field, replace
from fractions import Fraction
from importlib import resources
from types import MappingProxyType
from typing import TYPE_CHECKING, Mapping, Optional

from .constants import (
    BASE_HP_INCREASE,
    BASE_STAT_INCREASE,
    CRITICAL_MULTIPLIER,
    DAMAGE_DIVISOR,
    DAMAGE_LEVEL_DIVISOR,
    LEVEL_DOUBLES,
    MAX_TOTAL_TRAINING,
    MAX_TRAINING_PER_STAT,
    MAX_STAT_STAGE,
    MIN_STAT_STAGE,
    RANDOM_PERCENTAGES,
    DOUBLES_SCREEN_MULTIPLIER,
    SCREEN_MULTIPLIER,
    STAB_MULTIPLIER,
    STAT_STAGE_MULTIPLIERS,
    TYPES,
)

if TYPE_CHECKING:
    from .damage import DamageRolls
    from .pokemon import Pokemon


@dataclass(frozen=True)
class BattleLogic:
    """Immutable rules and constants for one game-logic version."""

    name: str
    level: int = LEVEL_DOUBLES
    base_hp_increase: int = BASE_HP_INCREASE
    base_stat_increase: int = BASE_STAT_INCREASE
    max_training_per_stat: int = MAX_TRAINING_PER_STAT
    max_total_training: int = MAX_TOTAL_TRAINING
    min_stat_stage: int = MIN_STAT_STAGE
    max_stat_stage: int = MAX_STAT_STAGE
    stat_stage_multipliers: Mapping[int, tuple[int, int]] = field(
        default_factory=lambda: MappingProxyType(dict(STAT_STAGE_MULTIPLIERS))
    )
    damage_level_divisor: int = DAMAGE_LEVEL_DIVISOR
    damage_divisor: int = DAMAGE_DIVISOR
    random_percentages: range = RANDOM_PERCENTAGES
    stab_multiplier: Fraction = STAB_MULTIPLIER
    critical_multiplier: Fraction = CRITICAL_MULTIPLIER
    screen_multiplier: Fraction = DOUBLES_SCREEN_MULTIPLIER
    type_chart: Optional[Mapping[str, Mapping[str, Fraction]]] = None

    def with_type_chart(
        self, type_chart: Mapping[str, Mapping[str, Fraction]]
    ) -> "BattleLogic":
        """Return this logic with an immutable type chart."""
        immutable_chart = MappingProxyType({
            attack: MappingProxyType(dict(defending))
            for attack, defending in type_chart.items()
        })
        return replace(self, type_chart=immutable_chart)

    def calculate_damage(
        self,
        attacker: "Pokemon",
        defender: "Pokemon",
        power: int,
        move_type: str,
        special: bool = False,
        percentage: bool = True,
        light_screen: bool = False,
        reflect: bool = False,
        aurora_veil: bool = False,
        helping_hand: bool = False,
        spread: bool = False,
    ) -> "DamageRolls":
        """Calculate damage using this battle logic and two Pokémon.

        Both Pokémon must use this exact logic instance. This makes the
        selected rule set explicit at the calculation call site.
        """
        from .damage import calculate_damage

        if attacker.battle_logic is not self or defender.battle_logic is not self:
            raise ValueError(
                "attacker and defender must use this battle logic"
            )
        return calculate_damage(
            attacker,
            defender,
            power,
            move_type,
            special=special,
            percentage=percentage,
            light_screen=light_screen,
            reflect=reflect,
            aurora_veil=aurora_veil,
            helping_hand=helping_hand,
            spread=spread,
        )


def _load_type_chart() -> Mapping[str, Mapping[str, Fraction]]:
    """Load the initial packaged type chart used by current battle logic."""
    path = resources.files("pyvgc.data").joinpath("initial_type_chart.csv")
    with path.open(newline="", encoding="utf-8") as file:
        return MappingProxyType({
            row["AttackingType"]: MappingProxyType({
                defending: Fraction(row[defending]) for defending in TYPES
            })
            for row in csv.DictReader(file)
        })


CARTRIDGE_CHAMPIONS_RELEASE_2026 = BattleLogic(
    name="Cartridge-Champions-Release-2026",
    type_chart=_load_type_chart(),
)

SIMULATOR_CHAMPIONS_RELEASE_2026 = replace(
    CARTRIDGE_CHAMPIONS_RELEASE_2026,
    name="Simulator-Champions-Release-2026",
)

CHAMPIONS_SINGLES = replace(
    CARTRIDGE_CHAMPIONS_RELEASE_2026,
    name="Champions-Singles-2026",
    screen_multiplier=SCREEN_MULTIPLIER,
)

BATTLE_LOGICS = MappingProxyType(
    {
        "Cartridge-Champions-Release-2026": CARTRIDGE_CHAMPIONS_RELEASE_2026,
        "Simulator-Champions-Release-2026": SIMULATOR_CHAMPIONS_RELEASE_2026,
        "Champions-Singles-2026": CHAMPIONS_SINGLES,
    }
)


def get_battle_logic(name: str) -> BattleLogic:
    """Return a registered battle logic by case-insensitive name."""
    if not isinstance(name, str) or not name.strip():
        raise ValueError("battle logic name must be a non-empty string")
    key = name.strip().casefold()
    for logic_name, logic in BATTLE_LOGICS.items():
        if logic_name.casefold() == key:
            return logic
    raise KeyError(f"Unknown battle logic: {name!r}")
