"""Supportive data-query utilities for pyvgc."""

import re
from collections.abc import Iterable, Mapping
from typing import Hashable, Optional, TypeVar, Union, cast

from .moves import Move
from .pokemon import Pokemon

_SHOWDOWN_STATS = {
    "hp": "hp",
    "atk": "attack",
    "def": "defense",
    "spa": "special_attack",
    "spd": "special_defense",
    "spe": "speed",
}
_SHOWDOWN_STAT_LABELS = {
    "hp": "HP",
    "attack": "Atk",
    "defense": "Def",
    "special_attack": "SpA",
    "special_defense": "SpD",
    "speed": "Spe",
}
_SHOWDOWN_EV_PATTERN = re.compile(r"^(\d+)\s+(HP|Atk|Def|SpA|SpD|Spe)$", re.I)
_TEAM_SIZE = 6
_TEAM_MEMBER_SCORE = 17
_MAX_TEAM_SCORE = _TEAM_SIZE * _TEAM_MEMBER_SCORE


TeamMember = Union[Pokemon, Mapping[str, object]]
Team = Iterable[TeamMember]
Identifier = TypeVar("Identifier", bound=Hashable)


def _team_member_values(member: TeamMember) -> tuple[
    str, Optional[str], Optional[str], Optional[str], tuple[str, ...]
]:
    if isinstance(member, Pokemon):
        name = member.name
        ability = member.ability
        item = member.get_item()
        nature = member.nature
        moves = member.moveset
    elif isinstance(member, Mapping):
        required_fields = {"name", "ability", "item", "nature", "moves"}
        missing_fields = required_fields - member.keys()
        if missing_fields:
            raise ValueError(
                "team member is missing required field(s): "
                + ", ".join(sorted(missing_fields))
            )
        name = member["name"]
        ability = member["ability"]
        item = member["item"]
        nature = member["nature"]
        moves = member["moves"]
    else:
        raise TypeError("team members must be Pokemon instances or mappings")

    if not isinstance(name, str) or not name.strip():
        raise ValueError("team member name must be a non-empty string")
    for field_name, value in (
        ("ability", ability),
        ("item", item),
        ("nature", nature),
    ):
        if value is not None and not isinstance(value, str):
            raise TypeError(f"team member {field_name} must be a string or None")
    if isinstance(moves, (str, bytes)) or not isinstance(moves, Iterable):
        raise TypeError("team member moves must be an iterable of moves")

    move_names = []
    for move in moves:
        if isinstance(move, Move):
            move_name = move.name
        elif isinstance(move, str):
            move_name = move
        else:
            raise TypeError("team member moves must be strings or Move instances")
        move_names.append(move_name)
    return name, ability, item, nature, tuple(move_names)


def _normalize_team(team: Team) -> tuple[
    tuple[str, Optional[str], Optional[str], Optional[str], tuple[str, ...]], ...
]:
    if isinstance(team, (str, bytes)) or not isinstance(team, Iterable):
        raise TypeError("team must be an iterable of Pokémon or team-member mappings")
    normalized = tuple(_team_member_values(member) for member in team)
    if len(normalized) != _TEAM_SIZE:
        raise ValueError(f"team must contain exactly {_TEAM_SIZE} Pokémon")
    names = [member[0].casefold() for member in normalized]
    if len(set(names)) != len(names):
        raise ValueError("team cannot contain duplicate Pokémon")
    return normalized


def compare_team_distance(team1: Team, team2: Team) -> int:
    """Return a team similarity score; higher scores indicate more similarity.

    Each team must contain six Pokémon. The maximum score is 102; a missing
    Pokémon costs 17 points, and each differing ability, item, nature, or move
    costs one point. Teams may be sequences of :class:`Pokemon` objects or
    mappings with ``name``, ``ability``, ``item``, ``nature``, and ``moves``.
    """
    first = _normalize_team(team1)
    second = _normalize_team(team2)
    second_by_name = {member[0].casefold(): member for member in second}
    score = _MAX_TEAM_SCORE

    for name, ability, item, nature, moves in first:
        other = second_by_name.get(name.casefold())
        if other is None:
            score -= _TEAM_MEMBER_SCORE
            continue
        _, other_ability, other_item, other_nature, other_moves = other
        score -= sum(
            value != other_value
            for value, other_value in (
                (ability, other_ability),
                (item, other_item),
                (nature, other_nature),
            )
        )
        score -= max(
            sum(move not in other_moves for move in moves),
            sum(move not in moves for move in other_moves),
        )
    return score


def _teams_from_records(
    teams: Mapping[Hashable, object],
) -> dict[Hashable, Team]:
    if not isinstance(teams, Mapping):
        raise TypeError("teams must be a mapping of team identifiers to teams")
    normalized: dict[Hashable, Team] = {}
    for identifier, record in teams.items():
        if isinstance(record, Mapping) and "team" in record:
            team = record["team"]
        else:
            team = record
        if isinstance(team, (str, bytes)) or not isinstance(team, Iterable):
            raise TypeError(
                f"team record {identifier!r} must contain an iterable team"
            )
        normalized[identifier] = cast(Team, team)
    return normalized


def pairwise_score_matrix(
    teams: Mapping[Hashable, object],
) -> dict[Hashable, dict[Hashable, int]]:
    """Return pairwise similarity scores for teams keyed by identifiers.

    Values may be six-Pokémon teams directly or records containing a ``team``
    field. The returned matrix is symmetric and includes self-comparisons.
    """
    team_map = _teams_from_records(teams)
    identifiers = list(team_map)
    return {
        identifier: {
            other_identifier: compare_team_distance(
                team_map[identifier],
                team_map[other_identifier],
            )
            for other_identifier in identifiers
        }
        for identifier in identifiers
    }


def find_team_pairs_by_score(
    score_matrix: Mapping[Identifier, Mapping[Identifier, int]],
    target_score: int,
) -> list[tuple[Identifier, Identifier, int]]:
    """Return distinct identifier pairs whose matrix score exactly matches."""
    if type(target_score) is not int:
        raise TypeError("target_score must be an integer")
    identifiers = list(score_matrix)
    pairs = []
    for identifier in identifiers:
        if not isinstance(score_matrix[identifier], Mapping):
            raise TypeError("score_matrix rows must be mappings")
    for index, identifier in enumerate(identifiers):
        row = score_matrix[identifier]
        for other_identifier in identifiers[index + 1:]:
            if other_identifier not in row:
                raise ValueError(
                    f"score_matrix row {identifier!r} is missing "
                    f"{other_identifier!r}"
                )
            score = row[other_identifier]
            if type(score) is not int:
                raise TypeError("score_matrix scores must be integers")
            if score == target_score:
                pairs.append((identifier, other_identifier, score))
    return pairs


def group_identical_teamplayers(
    score_matrix: Mapping[Identifier, Mapping[Identifier, int]],
) -> list[list[Identifier]]:
    """Group identifiers whose teams have the maximum similarity score of 102.

    Groups are connected components, so a chain of matching pairs joins its
    members. A score of 102 represents identical teams.
    """
    pairs = find_team_pairs_by_score(score_matrix, _MAX_TEAM_SCORE)
    neighbors: dict[Hashable, set[Hashable]] = {}
    for identifier, other_identifier, _ in pairs:
        neighbors.setdefault(identifier, set()).add(other_identifier)
        neighbors.setdefault(other_identifier, set()).add(identifier)

    groups = []
    visited = set()
    for identifier in neighbors:
        if identifier in visited:
            continue
        group = set()
        pending = [identifier]
        while pending:
            current = pending.pop()
            if current in visited:
                continue
            visited.add(current)
            group.add(current)
            pending.extend(neighbors[current] - visited)
        groups.append(
            [candidate for candidate in score_matrix if candidate in group]
        )
        if any(
            score_matrix[left].get(right) != _MAX_TEAM_SCORE
            or score_matrix[right].get(left) != _MAX_TEAM_SCORE
            for index, left in enumerate(groups[-1])
            for right in groups[-1][index + 1:]
        ):
            raise ValueError(
                "score_matrix must mark all pairs in an identical-team "
                "group with the maximum score"
            )
    return groups


def import_showdown_pokemon(
    text: str,
    regulation: str,
) -> Pokemon:
    """Import one Showdown-formatted set as a regulation-bound Pokémon.

    Supported fields are nickname/species, an optional item, ability, level,
    EVs, nature, and up to four moves. The regulation must be supplied because
    the Showdown format does not identify a regulation. The package models
    level 50 only. Unrecognized or unsupported Showdown fields are rejected
    rather than discarded.

    Args:
        text: One Showdown-formatted Pokémon set.
        regulation: Regulation snapshot used to validate the set.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Showdown set must be a non-empty string")

    from .regulations import load_regulation

    snapshot = load_regulation(regulation)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    header = lines[0]
    item: Optional[str] = None
    if " @ " in header:
        header, item = header.rsplit(" @ ", 1)
        header = header.strip()
        item = item.strip()
        if not item:
            raise ValueError("Showdown item name must not be empty")
    elif "@" in header:
        raise ValueError("Showdown item must be separated with ' @ '")

    pokemon_names = {name.casefold(): name for name in snapshot.pokemon_names}
    nickname = None
    species_name = header
    if species_name.casefold() not in pokemon_names:
        nickname_part, separator, species_part = header.rpartition(" (")
        if separator and species_part.endswith(")"):
            nickname = nickname_part.strip()
            species_name = species_part[:-1].strip()
            if not nickname or not species_name:
                raise ValueError("Showdown nickname/species line is malformed")

    fields: dict[str, str] = {}
    moves: list[str] = []
    for line_number, line in enumerate(lines[1:], start=2):
        if line.startswith("-"):
            move_name = line[1:].strip()
            if not move_name:
                raise ValueError(
                    f"Showdown move on line {line_number} must not be empty"
                )
            moves.append(move_name)
            continue
        if line.casefold().endswith(" nature"):
            field_name = "nature"
            value = line[:-7].strip()
            if field_name in fields:
                raise ValueError(
                    f"Duplicate Showdown field on line {line_number}: "
                    f"{field_name!r}"
                )
            fields[field_name] = value
            continue
        field_name, separator, value = line.partition(":")
        if not separator:
            raise ValueError(
                f"Unsupported Showdown line {line_number}: {line!r}"
            )
        field_name = field_name.strip().casefold()
        if field_name not in {"ability", "level", "evs", "nature"}:
            raise ValueError(
                f"Unsupported Showdown field on line {line_number}: "
                f"{field_name!r}"
            )
        if field_name in fields:
            raise ValueError(
                f"Duplicate Showdown field on line {line_number}: "
                f"{field_name!r}"
            )
        fields[field_name] = value.strip()

    if "level" in fields:
        try:
            level = int(fields["level"])
        except ValueError:
            raise ValueError("Showdown level must be an integer") from None
        if level != snapshot.battle_logic.level:
            raise ValueError(
                f"Only level {snapshot.battle_logic.level} Pokémon are supported"
            )

    stat_training: dict[str, int] = {}
    if "evs" in fields and fields["evs"]:
        for allocation in fields["evs"].split("/"):
            match = _SHOWDOWN_EV_PATTERN.fullmatch(allocation.strip())
            if match is None:
                raise ValueError(
                    f"Invalid Showdown EV allocation: {allocation.strip()!r}"
                )
            amount, stat_label = match.groups()
            stat_name = _SHOWDOWN_STATS[stat_label.casefold()]
            if stat_name in stat_training:
                raise ValueError(
                    f"Duplicate Showdown EV allocation for {stat_label}"
                )
            stat_training[stat_name] = int(amount)

    return snapshot.load_pokemon(
        species_name,
        stat_training=stat_training,
        nature=fields.get("nature"),
        item=item,
        moveset=moves,
        nickname=nickname,
        ability=fields.get("ability"),
    )


def export_showdown_pokemon(pokemon: Pokemon) -> str:
    """Export a Pokémon as a Showdown-formatted set.

    Exports fields represented by pyvgc: nickname, species, optional item,
    ability, level, training values, nature, and equipped moves.
    """
    if not isinstance(pokemon, Pokemon):
        raise TypeError("pokemon must be a Pokemon instance")

    display_name = pokemon.name
    if pokemon.nickname is not None:
        display_name = f"{pokemon.nickname} ({pokemon.name})"
    if pokemon.get_item() is not None:
        display_name += f" @ {pokemon.get_item()}"

    lines = [display_name]
    if pokemon.ability is not None:
        lines.append(f"Ability: {pokemon.ability}")
    lines.append(f"Level: {pokemon.battle_logic.level}")

    allocations = [
        f"{amount} {_SHOWDOWN_STAT_LABELS[stat]}"
        for stat, amount in pokemon.stat_training.items()
        if amount
    ]
    if allocations:
        lines.append(f"EVs: {' / '.join(allocations)}")
    if pokemon.nature is not None:
        lines.append(f"{pokemon.nature} Nature")
    lines.extend(f"- {move.name}" for move in pokemon.moveset)
    return "\n".join(lines)


def get_movepool_for_pokemon(
    name: str,
    regulation: str,
) -> tuple[Move, ...]:
    """Return a Pokémon's legal movepool for a regulation.

    Args:
        name: Pokémon form name.
        regulation: Regulation snapshot name, such as ``"M-C"``.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Pokémon name must be a non-empty string")
    from .regulations import load_regulation

    try:
        return load_regulation(regulation).get_movepool_for_pokemon(name)
    except KeyError:
        raise KeyError(
            f"Pokémon not found in Pokémon Champions movepools: {name!r}"
        ) from None


def get_pokemon_for_move(
    name: str,
    regulation: str = "M-C",
) -> tuple[str, ...]:
    """Return all forms whose movepool contains a move in a regulation.

    Args:
        name: Move name.
        regulation: Regulation snapshot name, such as ``"M-C"``.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("move name must be a non-empty string")
    from .regulations import load_regulation

    snapshot = load_regulation(regulation)
    move_name = snapshot.move(name).name
    return snapshot._pokemon_by_move.get(move_name.casefold(), ())


def pokemon_with_single_ability(regulation: str) -> tuple[str, ...]:
    """Return forms with exactly one recorded ability.

    Args:
        regulation: Regulation snapshot name, such as ``"M-B"``.

    Returns:
        Canonically named forms sorted case-insensitively.
    """
    from .regulations import load_regulation

    snapshot = load_regulation(regulation)
    return tuple(sorted(
        (
            pokemon_name
            for pokemon_name, abilities in snapshot.abilities.items()
            if len(abilities) == 1
        ),
        key=str.casefold,
    ))


def pokemon_with_ability(
    regulation: str,
    ability: str,
) -> tuple[str, ...]:
    """Return forms that have a named ability in a regulation.

    Args:
        regulation: Regulation snapshot name, such as ``"M-B"``.
        ability: Ability name to match, case-insensitively.

    Returns:
        Canonically named forms sorted case-insensitively.

    Raises:
        ValueError: If ``ability`` is not a non-empty string.
    """
    if not isinstance(ability, str) or not ability.strip():
        raise ValueError("ability name must be a non-empty string")

    target = ability.strip().casefold()
    from .regulations import load_regulation

    snapshot = load_regulation(regulation)
    return tuple(sorted(
        (
            pokemon_name
            for pokemon_name, abilities in snapshot.abilities.items()
            if any(recorded.casefold() == target for recorded in abilities)
        ),
        key=str.casefold,
    ))


def regulation_description(regulation: str) -> str:
    """Return one line containing the content counts for a regulation.

    The returned format is ``"Pokémon: X, Items: Y, Moves: Z"``.

    Args:
        regulation: Regulation snapshot name, such as ``"M-C"``.
    """
    from .regulations import load_regulation

    snapshot = load_regulation(regulation)
    return (
        f"Pokémon: {len(snapshot.pokemon_names)}, "
        f"Items: {len(snapshot.items)}, "
        f"Moves: {len(snapshot.moves)}"
    )


def signature_moves(regulation: str) -> tuple[tuple[str, str], ...]:
    """Return moves in the movepool of exactly one Pokémon species.

    Each result is a ``(move_name, pokemon_name)`` pair. Pokémon forms are
    grouped by their shared roster number, so a move learned by a base form
    and its Mega or alternate forms is still signature to that species. Every
    form that learns the signature move is included in the result.

    Args:
        regulation: Regulation snapshot name, such as ``"M-C"``.

    Returns:
        Signature move and Pokémon-form pairs sorted by move and form name.
    """
    from .regulations import load_regulation

    snapshot = load_regulation(regulation)
    return snapshot._signature_move_index
