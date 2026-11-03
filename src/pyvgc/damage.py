"""Pokémon Champions damage calculation for level-50 Pokémon."""

from __future__ import annotations

from fractions import Fraction
from typing import TYPE_CHECKING, Iterable, TypedDict

from .constants import TYPES
from .moves import Move

if TYPE_CHECKING:
    from .battle_logic import BattleLogic
    from .pokemon import Pokemon

SPREAD_MULTIPLIER = Fraction(3, 4)
HELPING_HAND_MULTIPLIER = Fraction(3, 2)


class DamageRolls(TypedDict, total=False):
    """Mapping returned by damage calculations."""

    normal: list[int]
    critical: list[int]
    normal_percentage: list[float]
    critical_percentage: list[float]


def _normalize_type(type_name: str) -> str:
    """Validate and canonicalize one Pokémon type name."""
    if not isinstance(type_name, str):
        raise ValueError(f"type names must be strings, got {type(type_name).__name__}")
    normalized = type_name.strip().title()
    if normalized not in TYPES:
        raise ValueError(f"unknown Pokémon type: {type_name!r}")
    return normalized


def _type_multiplier_for_types(
    move_type: str, defender_types: tuple[str, ...], logic: BattleLogic
) -> Fraction:
    """Return effectiveness for already-normalized defender types."""
    if logic.type_chart is None:
        raise ValueError(f"battle logic {logic.name!r} has no type chart")
    multiplier = Fraction(1)
    for defender_type in defender_types:
        multiplier *= logic.type_chart[move_type][defender_type]
    return multiplier


def _type_multiplier(
    move_type: str, defender_types: Iterable[str], logic: BattleLogic
) -> Fraction:
    """Normalize types and return their combined effectiveness multiplier."""
    normalized_move = _normalize_type(move_type)
    normalized_defenders = tuple(
        _normalize_type(defender_type) for defender_type in defender_types
    )
    return _type_multiplier_for_types(
        normalized_move, normalized_defenders, logic
    )


def _screen_multiplier(
    logic: BattleLogic,
    critical: bool,
    special: bool,
    light_screen: bool,
    reflect: bool,
    aurora_veil: bool,
) -> Fraction:
    """Return the one applicable screen multiplier for a damage roll."""
    if critical:
        return Fraction(1)
    screen_active = (
        aurora_veil
        or special and light_screen
        or not special and reflect
    )
    return logic.screen_multiplier if screen_active else Fraction(1)


def _resolve_move_parameters(
    power: int | Move | None,
    move_type: str | None,
    special: bool | None,
    move: Move | None,
    spread: bool | None,
) -> tuple[int, str, bool, bool]:
    """Resolve either a custom Move or the legacy raw damage parameters."""
    if move is not None:
        if power is not None or move_type is not None:
            raise ValueError("provide either move or power and move_type, not both")
        selected_move = move
    elif isinstance(power, Move):
        if move_type is not None:
            raise ValueError("move_type must not be provided with a Move")
        selected_move = power
    else:
        selected_move = None

    if selected_move is None:
        if power is None or move_type is None:
            raise ValueError("power and move_type are required without a Move")
        return power, move_type, bool(special), bool(spread)

    if not isinstance(selected_move, Move):
        raise TypeError("move must be a Move instance")
    if selected_move.category not in ("Physical", "Special"):
        raise ValueError("only Physical and Special moves can deal damage")
    if selected_move.base_power is None:
        raise ValueError("move must have a base power to calculate damage")
    move_is_special = selected_move.category == "Special"
    if special is not None and special != move_is_special:
        raise ValueError("special must match the Move category")
    move_is_spread = (
        selected_move.is_spread if spread is None else spread
    )
    return (
        selected_move.base_power,
        selected_move.type,
        move_is_special,
        move_is_spread,
    )


def damage_rolls(
    power: int | Move | None,
    attack: int,
    defense: int,
    move_type: str | None,
    attacker_types: Iterable[str],
    defender_types: Iterable[str],
    logic: BattleLogic,
    special: bool | None = None,
    light_screen: bool = False,
    reflect: bool = False,
    aurora_veil: bool = False,
    helping_hand: bool = False,
    spread: bool | None = None,
    move: Move | None = None,
) -> DamageRolls:
    """Return all 16 normal and 16 critical damage rolls.

    ``attack`` and ``defense`` are the already-calculated battle stats.
    Damage is floored at every formula step, as in the games. Critical hits
    use the selected logic's critical multiplier and ignore the relevant stat
    stages. Non-immune hits deal at least 1 damage. Modifier flags are disabled
    by default, the move's target metadata determines it. Set ``spread``
    explicitly to override that metadata.
    """
    power, move_type, special, spread = _resolve_move_parameters(
        power, move_type, special, move, spread
    )
    if not all(
        type(value) is int and value > 0
        for value in (power, attack, defense)
    ):
        raise ValueError("power, attack, and defense must be positive integers")
    move_type = _normalize_type(move_type)
    attacker_types = tuple(
        _normalize_type(type_name) for type_name in attacker_types
    )
    defender_types = tuple(
        _normalize_type(type_name) for type_name in defender_types
    )
    if not attacker_types or not defender_types:
        raise ValueError("attacker_types and defender_types must not be empty")
    if len(attacker_types) > 2 or len(defender_types) > 2:
        raise ValueError("a Pokémon can have at most two types")
    stab = logic.stab_multiplier if move_type in attacker_types else Fraction(1)
    effectiveness = _type_multiplier(move_type, defender_types, logic)

    # (((((2L/5)+2) * Power * A / D) / 50) + 2), with integer floors.
    base = (
        (
            (2 * logic.level // logic.damage_level_divisor + 2)
            * power
            * attack
            // defense
        )
        // logic.damage_divisor
    ) + 2
    if helping_hand:
        base = int((base - 2) * HELPING_HAND_MULTIPLIER) + 2
    if spread:
        base = int(base * SPREAD_MULTIPLIER)

    def rolls(critical: bool) -> list[int]:
        """Calculate all 16 random outcomes for one hit category."""
        result: list[int] = []
        critical_damage = int(base * logic.critical_multiplier) if critical else base
        screen_multiplier = _screen_multiplier(
            logic,
            critical=critical,
            special=special,
            light_screen=light_screen,
            reflect=reflect,
            aurora_veil=aurora_veil,
        )
        for random_percent in logic.random_percentages:
            fixed = critical_damage * random_percent // 100
            fixed = int(fixed * stab)
            fixed = int(fixed * effectiveness)
            if not critical:
                fixed = int(fixed * screen_multiplier)
            if effectiveness:
                fixed = max(1, fixed)
            result.append(fixed)
        return result

    return {"normal": rolls(False), "critical": rolls(True)}


def calculate_damage(
    attacker: "Pokemon",
    defender: "Pokemon",
    power: int | Move | None = None,
    move_type: str | None = None,
    special: bool | None = None,
    percentage: bool = True,
    light_screen: bool = False,
    reflect: bool = False,
    aurora_veil: bool = False,
    helping_hand: bool = False,
    spread: bool | None = None,
    move: Move | None = None,
) -> DamageRolls:
    """Calculate damage rolls using two Pokémon and their current battle state.

    The Pokémon models provide state only. This function owns the damage
    calculation, including critical-hit stat-stage handling and percentages.
    Other modifier flags are disabled by default. When a move object is
    provided, its spread metadata is used unless ``spread`` is explicitly set.
    Raw power/type calculations default to single-target behavior.
    """
    from .pokemon import Pokemon

    power, move_type, special, spread = _resolve_move_parameters(
        power, move_type, special, move, spread
    )
    if not isinstance(attacker, Pokemon) or not isinstance(defender, Pokemon):
        raise TypeError("attacker and defender must be Pokemon instances")
    if attacker.battle_logic is not defender.battle_logic:
        raise ValueError("attacker and defender must use the same battle logic")

    attack_stat = "special_attack" if special else "attack"
    defense_stat = "special_defense" if special else "defense"
    attack = getattr(attacker, attack_stat)
    defense = getattr(defender, defense_stat)
    rolls = damage_rolls(
        power,
        attack,
        defense,
        move_type,
        attacker.types,
        defender.types,
        logic=attacker.battle_logic,
        special=special,
        light_screen=light_screen,
        reflect=reflect,
        aurora_veil=aurora_veil,
        helping_hand=helping_hand,
        spread=spread,
    )
    critical_attack = (
        attacker._pre_stage_stats[attack_stat]
        if attacker._stat_stages.get(attack_stat, 0) < 0
        else attack
    )
    critical_defense = (
        defender._pre_stage_stats[defense_stat]
        if defender._stat_stages.get(defense_stat, 0) > 0
        else defense
    )
    if critical_attack != attack or critical_defense != defense:
        rolls["critical"] = damage_rolls(
            power,
            critical_attack,
            critical_defense,
            move_type,
            attacker.types,
            defender.types,
            logic=attacker.battle_logic,
            special=special,
            light_screen=light_screen,
            reflect=reflect,
            aurora_veil=aurora_veil,
            helping_hand=helping_hand,
            spread=spread,
        )["critical"]
    if percentage:
        rolls["normal_percentage"] = [
            round(damage / defender.hp * 100, 2)
            for damage in rolls["normal"]
        ]
        rolls["critical_percentage"] = [
            round(damage / defender.hp * 100, 2)
            for damage in rolls["critical"]
        ]
    return rolls
